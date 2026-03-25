import gzip
from io import BytesIO
from flask import request, after_this_request


def compress_response(response):
    """Compress response with gzip if client supports it"""
    if 'gzip' not in request.headers.get('Accept-Encoding', ''):
        return response
    
    # Don't compress small responses
    if response.content_length and response.content_length < 1000:
        return response
    
    # Compress response
    gzip_buffer = BytesIO()
    with gzip.GzipFile(mode='wb', fileobj=gzip_buffer, compresslevel=6) as gzip_file:
        gzip_file.write(response.get_data())
    
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())
    
    return response