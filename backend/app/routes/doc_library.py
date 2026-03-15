"""
Document library management routes.
"""

import os
import uuid
import threading
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from app.utils.auth import token_required
from app.models.doc_library import (
    LIBRARY_TYPES,
    get_library_dir, ensure_user_doc_dir,
    create_library, get_library, get_all_libraries, update_library, delete_library,
    add_document, get_document, get_library_documents, delete_document,
    get_conversation_libraries, set_conversation_libraries, validate_conversation_libraries,
    get_embedding_status, set_embedding_status, update_embedding_progress,
    update_library_stats
)
from app.models.model_config import is_embedding_configured
from app.services.rag_service import get_rag_service
from app.services.embedding_service import reload_embedding_service

doc_library_bp = Blueprint('doc_library', __name__)

ALLOWED_EXTENSIONS = {'txt', 'md'}

_upload_sessions = {}
_upload_lock = threading.Lock()


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============ Library Routes ============

@doc_library_bp.route('/types', methods=['GET'])
@token_required
def get_library_types():
    """Get available library types."""
    return jsonify({'types': LIBRARY_TYPES})


@doc_library_bp.route('/', methods=['GET'])
@token_required
def list_libraries():
    """Get all libraries for the current user."""
    user_id = g.user['id']
    libraries = get_all_libraries(user_id)
    return jsonify({'libraries': libraries})


@doc_library_bp.route('/', methods=['POST'])
@token_required
def create_new_library():
    """Create a new document library."""
    user_id = g.user['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    name = data.get('name', '').strip()
    library_type = data.get('type', '')
    
    if not name:
        return jsonify({'error': '请输入文档库名称'}), 400
    
    if library_type not in LIBRARY_TYPES:
        return jsonify({'error': f'无效的文档库类型，必须是: {", ".join(LIBRARY_TYPES)}'}), 400
    
    try:
        library = create_library(user_id, name, library_type)
        return jsonify({'library': library}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doc_library_bp.route('/<library_id>', methods=['GET'])
@token_required
def get_library_detail(library_id):
    """Get a library by ID."""
    user_id = g.user['id']
    library = get_library(user_id, library_id)
    
    if not library:
        return jsonify({'error': '文档库不存在'}), 404
    
    return jsonify({'library': library})


@doc_library_bp.route('/<library_id>', methods=['PUT'])
@token_required
def update_library_info(library_id):
    """Update a library's metadata."""
    user_id = g.user['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    # Check if library exists
    existing = get_library(user_id, library_id)
    if not existing:
        return jsonify({'error': '文档库不存在'}), 404
    
    try:
        library = update_library(
            user_id, library_id,
            name=data.get('name'),
            library_type=data.get('type')
        )
        return jsonify({'library': library})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@doc_library_bp.route('/<library_id>', methods=['DELETE'])
@token_required
def delete_library_route(library_id):
    """Delete a library and all its documents."""
    user_id = g.user['id']
    
    # Check embedding status
    status = get_embedding_status(user_id)
    if status['is_embedding'] and status.get('current_library_id') == library_id:
        return jsonify({'error': '该文档库正在处理中，无法删除'}), 400
    
    success = delete_library(user_id, library_id)
    
    if not success:
        return jsonify({'error': '文档库不存在'}), 404
    
    # Invalidate index cache
    get_rag_service().invalidate_index_cache(user_id, library_id)
    
    return jsonify({'message': '文档库删除成功'})


# ============ Document Routes ============

@doc_library_bp.route('/<library_id>/documents', methods=['GET'])
@token_required
def list_documents(library_id):
    """Get all documents in a library."""
    user_id = g.user['id']
    
    library = get_library(user_id, library_id)
    if not library:
        return jsonify({'error': '文档库不存在'}), 404
    
    documents = get_library_documents(user_id, library_id)
    return jsonify({'documents': documents})


@doc_library_bp.route('/<library_id>/documents', methods=['POST'])
@token_required
def upload_document(library_id):
    """Upload a document to a library."""
    user_id = g.user['id']
    
    # Check if embedding is configured
    if not is_embedding_configured():
        return jsonify({'error': 'Embedding模型未配置，请联系管理员'}), 400
    
    library = get_library(user_id, library_id)
    if not library:
        return jsonify({'error': '文档库不存在'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型，仅支持 .txt 和 .md 文件'}), 400
    
    original_filename = secure_filename(file.filename)
    if not original_filename:
        original_filename = 'document.txt'
    
    # Generate unique filename
    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'txt'
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    
    # Save file
    library_dir = get_library_dir(user_id, library_id)
    files_dir = os.path.join(library_dir, "files")
    os.makedirs(files_dir, exist_ok=True)
    
    file_path = os.path.join(files_dir, unique_filename)
    
    try:
        file.save(file_path)
        
        # Validate file can be read as UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        
        file_size = os.path.getsize(file_path)
        
        doc = add_document(user_id, library_id, unique_filename, original_filename, file_size)
        
        return jsonify({'document': doc}), 201
        
    except UnicodeDecodeError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': '文件编码错误，请确保文件为UTF-8编码'}), 400
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500


@doc_library_bp.route('/<library_id>/documents/<doc_id>', methods=['DELETE'])
@token_required
def delete_document_route(library_id, doc_id):
    """Delete a document from a library."""
    user_id = g.user['id']
    
    # Check embedding status
    status = get_embedding_status(user_id)
    if status['is_embedding'] and status.get('current_document_id') == doc_id:
        return jsonify({'error': '该文档正在处理中，无法删除'}), 400
    
    doc = get_document(user_id, doc_id)
    if not doc or doc['library_id'] != library_id:
        return jsonify({'error': '文档不存在'}), 404
    
    # Remove from FAISS index first
    if doc['status'] == 'completed':
        get_rag_service().remove_document_from_index(user_id, library_id, doc_id)
    
    success = delete_document(user_id, doc_id)
    
    if not success:
        return jsonify({'error': '文档不存在'}), 404
    
    return jsonify({'message': '文档删除成功'})


# ============ Embedding Routes ============

@doc_library_bp.route('/<library_id>/start-embedding', methods=['POST'])
@token_required
def start_embedding(library_id):
    """Start embedding process for pending documents in a library."""
    user_id = g.user['id']
    
    # Check if embedding is configured
    if not is_embedding_configured():
        return jsonify({'error': 'Embedding模型未配置，请联系管理员'}), 400
    
    # Check current embedding status
    status = get_embedding_status(user_id)
    if status['is_embedding']:
        return jsonify({'error': '已有文档正在处理中'}), 400
    
    library = get_library(user_id, library_id)
    if not library:
        return jsonify({'error': '文档库不存在'}), 404
    
    # Get pending documents
    documents = get_library_documents(user_id, library_id)
    pending_docs = [d for d in documents if d['status'] == 'pending']
    
    if not pending_docs:
        return jsonify({'error': '没有待处理的文档'}), 400
    
    # Reload embedding service to get latest config
    reload_embedding_service()
    
    # Start embedding in background thread
    def process_documents():
        try:
            set_embedding_status(user_id, True, library_id)
            rag_service = get_rag_service()
            
            total_docs = len(pending_docs)
            for i, doc in enumerate(pending_docs):
                # Check if cancelled
                current_status = get_embedding_status(user_id)
                if not current_status['is_embedding']:
                    break
                
                update_embedding_progress(user_id, i / total_docs * 100, doc['id'])
                
                file_path = os.path.join(
                    get_library_dir(user_id, library_id),
                    "files",
                    doc['filename']
                )
                
                def progress_callback(progress):
                    overall = (i + progress) / total_docs * 100
                    update_embedding_progress(user_id, overall, doc['id'])
                
                rag_service.process_document(
                    user_id, library_id, doc['id'], file_path,
                    progress_callback=progress_callback
                )
            
        finally:
            set_embedding_status(user_id, False)
            update_library_stats(user_id, library_id)
    
    thread = threading.Thread(target=process_documents, daemon=True)
    thread.start()
    
    return jsonify({
        'message': '开始处理文档',
        'pending_count': len(pending_docs)
    })


@doc_library_bp.route('/embedding-status', methods=['GET'])
@token_required
def get_user_embedding_status():
    """Get current embedding status for the user."""
    user_id = g.user['id']
    status = get_embedding_status(user_id)
    return jsonify({'status': status})


@doc_library_bp.route('/stop-embedding', methods=['POST'])
@token_required
def stop_embedding():
    """Stop the current embedding process."""
    user_id = g.user['id']
    
    status = get_embedding_status(user_id)
    if not status['is_embedding']:
        return jsonify({'error': '没有正在进行的处理'}), 400
    
    set_embedding_status(user_id, False)
    
    return jsonify({'message': '已停止处理'})


# ============ Conversation Library Binding Routes ============

@doc_library_bp.route('/conversation/<conversation_id>/libraries', methods=['GET'])
@token_required
def get_conv_libraries(conversation_id):
    """Get libraries bound to a conversation."""
    user_id = g.user['id']
    
    # Validate and auto-unbind deleted libraries
    deleted_ids = validate_conversation_libraries(user_id, conversation_id)
    
    libraries = get_conversation_libraries(user_id, conversation_id)
    
    return jsonify({
        'libraries': libraries,
        'deleted_library_ids': deleted_ids
    })


@doc_library_bp.route('/conversation/<conversation_id>/libraries', methods=['PUT'])
@token_required
def set_conv_libraries(conversation_id):
    """Set libraries bound to a conversation."""
    user_id = g.user['id']
    data = request.get_json()
    
    if not data or 'library_ids' not in data:
        return jsonify({'error': '未提供library_ids'}), 400
    
    library_ids = data['library_ids']
    
    if not isinstance(library_ids, list):
        return jsonify({'error': 'library_ids必须是数组'}), 400
    
    # Validate all library_ids exist
    for lib_id in library_ids:
        if not get_library(user_id, lib_id):
            return jsonify({'error': f'文档库 {lib_id} 不存在'}), 400
    
    set_conversation_libraries(user_id, conversation_id, library_ids)
    
    libraries = get_conversation_libraries(user_id, conversation_id)
    return jsonify({'libraries': libraries})


# ============ Search Route ============

@doc_library_bp.route('/search', methods=['POST'])
@token_required
def search_documents():
    """Search across libraries."""
    user_id = g.user['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    query = data.get('query', '').strip()
    library_ids = data.get('library_ids', [])
    top_k = data.get('top_k', config.RAG_TOP_K)
    
    if not query:
        return jsonify({'error': '请输入搜索内容'}), 400
    
    if not library_ids:
        return jsonify({'error': '请选择要搜索的文档库'}), 400
    
    # Check embedding status
    status = get_embedding_status(user_id)
    if status['is_embedding']:
        return jsonify({'error': '文档正在处理中，请稍后再试'}), 400
    
    try:
        rag_service = get_rag_service()
        results = rag_service.search(user_id, library_ids, query, top_k)
        return jsonify({'results': results})
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500
