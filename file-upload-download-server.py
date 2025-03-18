#!/usr/bin/env python3

"""
HTTP Upload/Download Server with Folder Navigation

A minimal HTTP server that supports file uploads and downloads
with folder navigation capabilities. Fixed for folder uploads.
"""

import http.server
import socketserver
import os
import sys
import argparse
import json
import urllib.parse
from functools import partial
from pathlib import Path
import socket
import signal
import subprocess
import mimetypes
import io
import cgi
import tempfile

# HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>File Upload & Download Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
            background-color: #f8f9fa;
            color: #212529;
        }
        
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #121212;
                color: #e0e0e0;
            }
        }
        
        h1, h2 {
            margin-top: 0;
            padding: 15px 0;
            border-bottom: 1px solid #dee2e6;
        }
        
        @media (prefers-color-scheme: dark) {
            h1, h2 {
                border-color: #444;
            }
        }
        
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .upload-section, .files-section {
            flex: 1;
            min-width: 300px;
            background-color: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        @media (prefers-color-scheme: dark) {
            .upload-section, .files-section {
                background-color: #1e1e1e;
                box-shadow: 0 4px 6px rgba(255,255,255,0.05);
            }
        }
        
        .navigation-bar {
            display: flex;
            align-items: center;
            padding: 10px;
            margin-bottom: 15px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow-x: auto;
            white-space: nowrap;
        }
        
        @media (prefers-color-scheme: dark) {
            .navigation-bar {
                background-color: #333;
            }
        }
        
        .navigation-bar a {
            color: #0d6efd;
            text-decoration: none;
            padding: 5px 10px;
            margin-right: 5px;
        }
        
        .navigation-bar a:hover {
            text-decoration: underline;
        }
        
        @media (prefers-color-scheme: dark) {
            .navigation-bar a {
                color: #6ea8fe;
            }
        }
        
        .current-path {
            font-weight: 500;
            margin-right: 10px;
        }
        
        .path-separator {
            margin: 0 5px;
            color: #6c757d;
        }
        
        .files-list {
            margin-top: 15px;
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
        }
        
        @media (prefers-color-scheme: dark) {
            .files-list {
                border-color: #444;
            }
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }
        
        @media (prefers-color-scheme: dark) {
            .file-item {
                border-color: #444;
            }
        }
        
        .file-item:last-child {
            border-bottom: none;
        }
        
        .file-item.folder {
            background-color: rgba(13, 110, 253, 0.05);
        }
        
        @media (prefers-color-scheme: dark) {
            .file-item.folder {
                background-color: rgba(110, 168, 254, 0.05);
            }
        }
        
        .file-info {
            display: flex;
            align-items: center;
            flex-grow: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-right: 15px;
        }
        
        .file-icon {
            margin-right: 10px;
            font-size: 1.2em;
        }
        
        .file-name {
            flex-grow: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .file-actions {
            display: flex;
            gap: 10px;
        }
        
        .file-link {
            color: #0d6efd;
            text-decoration: none;
        }
        
        .file-link:hover {
            text-decoration: underline;
        }
        
        @media (prefers-color-scheme: dark) {
            .file-link {
                color: #6ea8fe;
            }
        }
        
        .drop-area {
            border: 2px dashed #dee2e6;
            border-radius: 4px;
            padding: 25px;
            text-align: center;
            margin-bottom: 20px;
            cursor: pointer;
        }
        
        @media (prefers-color-scheme: dark) {
            .drop-area {
                border-color: #444;
            }
        }
        
        .drop-area.active {
            border-color: #0d6efd;
            background-color: rgba(13, 110, 253, 0.1);
        }
        
        .progress-container {
            display: none;
            margin-top: 15px;
        }
        
        progress {
            width: 100%;
            height: 15px;
            border-radius: 4px;
        }
        
        .progress-info {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 14px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        button {
            background-color: #0d6efd;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        
        button:hover {
            background-color: #0b5ed7;
        }
        
        .empty-message {
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        
        .status-message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        
        .status-message.success {
            background-color: rgba(25, 135, 84, 0.1);
            color: #19875e;
            border: 1px solid rgba(25, 135, 84, 0.2);
            display: block;
        }
        
        .status-message.error {
            background-color: rgba(220, 53, 69, 0.1);
            color: #dc3545;
            border: 1px solid rgba(220, 53, 69, 0.2);
            display: block;
        }
        
        .create-folder-container {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .create-folder-container input {
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        
        @media (prefers-color-scheme: dark) {
            .create-folder-container input {
                background-color: #333;
                color: #e0e0e0;
                border-color: #444;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            
            .upload-section, .files-section {
                width: 100%;
            }
        }

        /* Button group styling */
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <h1>File Upload & Download Server</h1>
    
    <div class="navigation-bar" id="navigationBar">
        <!-- Path navigation will be added here -->
    </div>
    
    <div class="container">
        <div class="upload-section">
            <h2>Upload Files</h2>
            <div class="drop-area" id="dropArea" role="region" aria-label="File upload area">
                <p>Drag & drop files here or click to select</p>
            </div>
            
            <div class="button-group">
                <button id="fileButton" aria-label="Select files to upload">Select Files</button>
                <button id="folderButton" aria-label="Select folders to upload">Select Folders</button>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data" style="display: none;">
                <input type="file" id="fileInput" name="files" multiple>
                <input type="file" id="folderInput" name="files" webkitdirectory directory multiple>
                <input type="hidden" id="pathInput" name="path" value="">
            </form>
            
            <div class="progress-container" id="progressContainer" role="progressbar" aria-label="Upload progress">
                <progress id="uploadProgress" value="0" max="100" aria-label="Upload progress percentage"></progress>
                <div class="progress-info">
                    <span id="progressText" aria-live="polite">0%</span>
                    <span id="progressSize" aria-live="polite">0 KB / 0 KB</span>
                </div>
            </div>
            
            <div class="status-message" id="statusMessage" role="alert" aria-live="polite"></div>
            
            <div class="create-folder-container">
                <label for="newFolderName" class="sr-only">New folder name</label>
                <input type="text" id="newFolderName" placeholder="New folder name" aria-label="Enter new folder name">
                <button id="createFolderButton" aria-label="Create new folder">Create Folder</button>
            </div>
        </div>
        
        <div class="files-section">
            <h2>Files & Folders</h2>
            <div class="files-list" id="filesList">
                <div class="empty-message">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const dropArea = document.getElementById('dropArea');
            const fileInput = document.getElementById('fileInput');
            const folderInput = document.getElementById('folderInput');
            const fileButton = document.getElementById('fileButton');
            const folderButton = document.getElementById('folderButton');
            const uploadForm = document.getElementById('uploadForm');
            const pathInput = document.getElementById('pathInput');
            const progressContainer = document.getElementById('progressContainer');
            const uploadProgress = document.getElementById('uploadProgress');
            const progressText = document.getElementById('progressText');
            const progressSize = document.getElementById('progressSize');
            const filesList = document.getElementById('filesList');
            const statusMessage = document.getElementById('statusMessage');
            const navigationBar = document.getElementById('navigationBar');
            const newFolderName = document.getElementById('newFolderName');
            const createFolderButton = document.getElementById('createFolderButton');
            
            // Current path (relative to server root)
            let currentPath = '';
            
            // Load file list on page load
            loadFilesList();
            
            // Set up event listeners
            fileButton.addEventListener('click', () => fileInput.click());
            folderButton.addEventListener('click', () => folderInput.click());
            
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    uploadFiles(fileInput.files);
                }
            });
            
            folderInput.addEventListener('change', () => {
                if (folderInput.files.length > 0) {
                    uploadFiles(folderInput.files);
                }
            });
            
            createFolderButton.addEventListener('click', () => {
                const folderName = newFolderName.value.trim();
                if (folderName) {
                    createFolder(folderName);
                    newFolderName.value = '';
                } else {
                    showStatusMessage('Please enter a folder name', 'error');
                }
            });
            
            // Drag and drop handling
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, () => {
                    dropArea.classList.add('active');
                });
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, () => {
                    dropArea.classList.remove('active');
                });
            });
            
            dropArea.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const items = dt.items;
                
                // Check if we have items (directory or files)
                if (items) {
                    // Handle directory upload using webkitGetAsEntry
                    handleDataTransferItems(items);
                } else if (dt.files.length > 0) {
                    // Fallback to direct file upload
                    uploadFiles(dt.files);
                }
            });

            // Handle directory entries
            async function handleDataTransferItems(items) {
                const entries = [];
                let totalFiles = 0;
                
                // Process all items
                for (let i = 0; i < items.length; i++) {
                    const entry = items[i].webkitGetAsEntry();
                    if (entry) {
                        entries.push(entry);
                    }
                }
                
                // Count total files first
                for (const entry of entries) {
                    if (entry.isFile) {
                        totalFiles++;
                    } else if (entry.isDirectory) {
                        totalFiles += await countFilesInDirectory(entry);
                    }
                }
                
                if (totalFiles === 0) {
                    showStatusMessage('No files found to upload', 'error');
                    return
                }
                
                // Now process the entries
                const formData = new FormData();
                formData.append('path', currentPath);
                
                showStatusMessage(`Preparing ${totalFiles} files for upload...`, 'success');
                
                for (const entry of entries) {
                    await processEntry(entry, formData, '');
                }
                
                // Send the form data
                if (formData.has('files')) {
                    uploadFormData(formData);
                } else {
                    showStatusMessage('No files found to upload', 'error');
                }
            }
            
            // Count files in a directory recursively
            function countFilesInDirectory(directoryEntry) {
                return new Promise((resolve) => {
                    let count = 0;
                    
                    function readEntries(directoryReader) {
                        directoryReader.readEntries(async (entries) => {
                            if (entries.length === 0) {
                                resolve(count);
                                return;
                            }
                            
                            for (const entry of entries) {
                                if (entry.isFile) {
                                    count++;
                                } else if (entry.isDirectory) {
                                    count += await countFilesInDirectory(entry);
                                }
                            }
                            
                            // Continue reading
                            readEntries(directoryReader);
                        });
                    }
                    
                    const reader = directoryEntry.createReader();
                    readEntries(reader);
                });
            }
            
            // Process a directory entry recursively
            function processEntry(entry, formData, path) {
                return new Promise((resolve) => {
                    if (entry.isFile) {
                        entry.file(file => {
                            const filePath = path ? `${path}/${file.name}` : file.name;
                            formData.append('files', file, filePath);
                            resolve();
                        });
                    }
                    else if (entry.isDirectory) {
                        const dirPath = path ? `${path}/${entry.name}` : entry.name;
                        const dirReader = entry.createReader();
                        
                        // Function to read all entries
                        function readEntries() {
                            dirReader.readEntries(async (entries) => {
                                if (entries.length === 0) {
                                    resolve();
                                    return;
                                }
                                
                                // Process each entry
                                for (const entry of entries) {
                                    await processEntry(entry, formData, dirPath);
                                }
                                
                                // Continue reading (readEntries only returns some entries at a time)
                                readEntries();
                            });
                        }
                        
                        readEntries();
                    }
                });
            }
            
            // Function to create folder
            function createFolder(folderName) {
                const data = {
                    name: folderName,
                    path: currentPath
                };
                
                fetch('/create_folder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => {
                    if (response.ok) {
                        showStatusMessage(`Folder '${folderName}' created successfully`, 'success');
                        loadFilesList(); // Reload file list
                    } else {
                        response.text().then(text => {
                            showStatusMessage(`Failed to create folder: ${text}`, 'error');
                        });
                    }
                })
                .catch(error => {
                    showStatusMessage(`Error creating folder: ${error.message}`, 'error');
                });
            }
            
            // Function to navigate to path
            function navigateTo(path) {
                currentPath = path;
                pathInput.value = path;
                loadFilesList();
                updateNavigationBar();
            }
            
            // Function to update navigation bar
            function updateNavigationBar() {
                navigationBar.innerHTML = '';
                
                // Add root link
                const rootLink = document.createElement('a');
                rootLink.href = '#';
                rootLink.textContent = 'Home';
                rootLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    navigateTo('');
                });
                navigationBar.appendChild(rootLink);
                
                // Add path segments
                if (currentPath) {
                    const segments = currentPath.split('/');
                    let path = '';
                    
                    segments.forEach((segment, index) => {
                        if (!segment) return;
                        
                        // Add separator
                        const separator = document.createElement('span');
                        separator.textContent = ' / ';
                        separator.className = 'path-separator';
                        navigationBar.appendChild(separator);
                        
                        path += (path ? '/' : '') + segment;
                        
                        const isLast = index === segments.length - 1;
                        
                        // Add segment link
                        const segmentLink = document.createElement('a');
                        segmentLink.href = '#';
                        segmentLink.textContent = segment;
                        
                        if (isLast) {
                            segmentLink.style.fontWeight = 'bold';
                        }
                        
                        segmentLink.addEventListener('click', (e) => {
                            e.preventDefault();
                            navigateTo(path);
                        });
                        
                        navigationBar.appendChild(segmentLink);
                    });
                }
            }
            
            // Function to upload files
            function uploadFiles(files) {
                // Use FormData for better compatibility
                const formData = new FormData();
                
                // Add the current path
                formData.append('path', currentPath);
                
                // Add all files
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    
                    // Handle folders and files
                    if (file.webkitRelativePath) {
                        // This is a folder upload
                        formData.append('files', file, file.webkitRelativePath);
                    } else {
                        // Regular file
                        formData.append('files', file, file.name);
                    }
                }
                
                uploadFormData(formData);
            }
            
            // Function to upload form data
            function uploadFormData(formData) {
                // Show progress container
                progressContainer.style.display = 'block';
                
                // Start the upload
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(text => {
                    showStatusMessage('Files uploaded successfully!', 'success');
                    loadFilesList(); // Reload the files list
                    
                    // Reset the file inputs
                    fileInput.value = '';
                    folderInput.value = '';
                    
                    // Hide progress after a delay
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                        uploadProgress.value = 0;
                        progressText.textContent = '0%';
                        progressSize.textContent = '0 KB / 0 KB';
                    }, 3000);
                })
                .catch(error => {
                    console.error('Upload error:', error);
                    showStatusMessage(`Upload failed: ${error.message}`, 'error');
                    progressContainer.style.display = 'none';
                });
            }
            
            // Function to load the files list
            function loadFilesList() {
                fetch(`/list?path=${encodeURIComponent(currentPath)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.files && data.files.length > 0) {
                            filesList.innerHTML = '';
                            
                            // Sort folders first, then files
                            data.files.sort((a, b) => {
                                if (a.is_dir && !b.is_dir) return -1;
                                if (!a.is_dir && b.is_dir) return 1;
                                return a.name.localeCompare(b.name);
                            });
                            
                            // Add parent directory if not in root
                            if (currentPath) {
                                const parentItem = document.createElement('div');
                                parentItem.className = 'file-item folder';
                                parentItem.style.cursor = 'pointer';
                                
                                const fileInfo = document.createElement('div');
                                fileInfo.className = 'file-info';
                                
                                const fileIcon = document.createElement('span');
                                fileIcon.className = 'file-icon';
                                fileIcon.textContent = '📁';
                                
                                const fileName = document.createElement('div');
                                fileName.className = 'file-name';
                                fileName.textContent = '.. (Parent Directory)';
                                
                                fileInfo.appendChild(fileIcon);
                                fileInfo.appendChild(fileName);
                                parentItem.appendChild(fileInfo);
                                
                                parentItem.addEventListener('click', () => {
                                    // Navigate to parent directory
                                    const parts = currentPath.split('/');
                                    parts.pop();
                                    navigateTo(parts.join('/'));
                                });
                                
                                filesList.appendChild(parentItem);
                            }
                            
                            data.files.forEach(file => {
                                const fileItem = document.createElement('div');
                                fileItem.className = `file-item${file.is_dir ? ' folder' : ''}`;
                                
                                const fileInfo = document.createElement('div');
                                fileInfo.className = 'file-info';
                                
                                const fileIcon = document.createElement('span');
                                fileIcon.className = 'file-icon';
                                fileIcon.textContent = file.is_dir ? '[DIR]' : '';
                                
                                const fileName = document.createElement('div');
                                fileName.className = 'file-name';
                                fileName.textContent = file.name;
                                
                                fileInfo.appendChild(fileIcon);
                                fileInfo.appendChild(fileName);
                                fileItem.appendChild(fileInfo);
                                
                                if (file.is_dir) {
                                    // Folder click navigates into folder
                                    fileItem.addEventListener('click', () => {
                                        const newPath = currentPath ? 
                                            `${currentPath}/${file.name}` : 
                                            file.name;
                                        navigateTo(newPath);
                                    });
                                } else {
                                    // File has download action
                                    const fileActions = document.createElement('div');
                                    fileActions.className = 'file-actions';
                                    
                                    const downloadLink = document.createElement('a');
                                    const filePath = currentPath ? 
                                        `${currentPath}/${file.name}` : 
                                        file.name;
                                    downloadLink.href = encodeURI(`/download?path=${encodeURIComponent(filePath)}`);
                                    downloadLink.className = 'file-link';
                                    downloadLink.textContent = 'Download';
                                    downloadLink.setAttribute('download', file.name);
                                    
                                    fileActions.appendChild(downloadLink);
                                    fileItem.appendChild(fileActions);
                                }
                                
                                filesList.appendChild(fileItem);
                            });
                        } else {
                            filesList.innerHTML = '<div class="empty-message">No files available in this directory</div>';
                        }
                        
                        // Update navigation bar
                        updateNavigationBar();
                    })
                    .catch(error => {
                        console.error('Error loading files list:', error);
                        filesList.innerHTML = '<div class="empty-message">Error loading files</div>';
                    });
            }
            
            // Function to show status message
            function showStatusMessage(message, type) {
                statusMessage.textContent = message;
                statusMessage.className = 'status-message ' + type;
                statusMessage.style.display = 'block';
                
                // Hide message after 5 seconds
                setTimeout(() => {
                    statusMessage.style.display = 'none';
                }, 5000);
            }
        });
    </script>
</body>
</html>
"""

# Main request handler
class FixedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.base_directory = directory
        super().__init__(*args, directory=directory, **kwargs)
    
    def end_headers(self):
        # Add security headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Content-Length, Accept')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '3600')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def get_full_path(self, rel_path):
        """Convert a relative path to a full path within the base directory"""
        # Sanitize path to prevent path traversal
        norm_path = os.path.normpath(rel_path)
        # Remove leading slash or dot
        if norm_path.startswith('/') or norm_path.startswith('./'):
            norm_path = norm_path[1:]
        # Ensure path doesn't escape base directory
        if norm_path == '..' or norm_path.startswith('../'):
            norm_path = ''
        
        return os.path.join(self.base_directory, norm_path)
    
    def do_GET(self):
        # Parse URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Handle root path - serve index page
        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
            return
        
        # Handle file list request
        elif path == "/list":
            try:
                # Get the requested path from query parameters
                query = urllib.parse.parse_qs(parsed_url.query)
                rel_path = query.get('path', [''])[0]
                full_path = self.get_full_path(rel_path)
                
                # Check if path exists and is directory
                if not os.path.exists(full_path):
                    self.send_error(404, "Directory not found")
                    return
                
                if not os.path.isdir(full_path):
                    self.send_error(400, "Path is not a directory")
                    return
                
                # List directory contents
                files = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    is_dir = os.path.isdir(item_path)
                    
                    # Skip hidden files and directories (starting with .)
                    if item.startswith('.'):
                        continue
                    
                    # Convert filename to ASCII-only
                    clean_name = ''.join(c for c in item if ord(c) < 128)
                    if not clean_name:
                        clean_name = 'unnamed_file'
                    
                    files.append({
                        "name": clean_name,
                        "is_dir": is_dir,
                        "size": 0 if is_dir else os.path.getsize(item_path),
                        "modified": os.path.getmtime(item_path)
                    })
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"files": files}).encode())
                return
                
            except Exception as e:
                print(f"Error listing directory: {str(e)}")
                self.send_error(500, f"Server error: {str(e)}")
                return
        
        # Handle download request
        elif path == "/download":
            try:
                # Get the requested path from query parameters
                query = urllib.parse.parse_qs(parsed_url.query)
                rel_path = query.get('path', [''])[0]
                
                # Decode the URL-encoded path
                rel_path = urllib.parse.unquote(rel_path)
                full_path = self.get_full_path(rel_path)
                
                print(f"Download request for path: {rel_path}")
                print(f"Full path: {full_path}")
                
                # Check if file exists
                if not os.path.exists(full_path):
                    print(f"File not found at path: {full_path}")
                    self.send_error(404, "File not found")
                    return
                
                if os.path.isdir(full_path):
                    print(f"Path is a directory: {full_path}")
                    self.send_error(400, "Cannot download a directory")
                    return
                
                # Get file size and type
                file_size = os.path.getsize(full_path)
                content_type, _ = mimetypes.guess_type(full_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                print(f"File size: {file_size} bytes")
                print(f"Content type: {content_type}")
                
                # Send file
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(full_path)}"')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                
                print(f"Successfully sent file: {full_path}")
                return
                
            except Exception as e:
                print(f"Error serving file: {str(e)}")
                self.send_error(500, f"Server error: {str(e)}")
                return
        
        # Serve regular files
        super().do_GET()

    def do_POST(self):
        # Parse URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Handle folder creation
        if path == "/create_folder":
            try:
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_error(400, "No content provided")
                    return
                
                # Read the request body
                data = self.rfile.read(content_length)
                folder_data = json.loads(data.decode('utf-8'))
                
                # Get folder name and path
                folder_name = folder_data.get('name', '').strip()
                rel_path = folder_data.get('path', '').strip()
                
                if not folder_name:
                    self.send_error(400, "Folder name is required")
                    return
                
                # Validate and create full path
                full_path = self.get_full_path(rel_path)
                new_folder_path = os.path.join(full_path, folder_name)
                
                # Check if folder already exists
                if os.path.exists(new_folder_path):
                    self.send_error(400, "Folder already exists")
                    return
                
                # Create the folder
                try:
                    os.makedirs(new_folder_path, exist_ok=True)
                    print(f"Created folder: {new_folder_path}")
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write("Folder created successfully".encode())
                except Exception as e:
                    print(f"Error creating folder: {str(e)}")
                    self.send_error(500, f"Cannot create folder: {str(e)}")
                return
                
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON data")
                return
            except Exception as e:
                print(f"Error handling folder creation: {str(e)}")
                self.send_error(500, f"Server error: {str(e)}")
                return
        
        # Handle file upload
        elif path == "/upload":
            try:
                # Parse the form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type'],
                    }
                )
                
                # Get target path
                target_path = form.getfirst('path', '').strip()
                
                # Validate and create full path
                full_target_path = self.get_full_path(target_path)
                print(f"Full target path: {full_target_path}")
                
                # Ensure target directory exists
                if not os.path.exists(full_target_path):
                    try:
                        os.makedirs(full_target_path, exist_ok=True)
                        print(f"Created target directory: {full_target_path}")
                    except Exception as e:
                        print(f"Error creating directory {full_target_path}: {str(e)}")
                        self.send_error(500, f"Cannot create directory: {str(e)}")
                        return
                
                # Process uploaded files
                files_saved = 0
                
                # Get all file items
                if 'files' in form:
                    file_items = form['files']
                    if not isinstance(file_items, list):
                        file_items = [file_items]
                    
                    for item in file_items:
                        if item.filename:
                            filename = item.filename
                            
                            # Handle files in folders (with path separators)
                            if '/' in filename or '\\' in filename:
                                # Normalize path separators to forward slashes
                                normalized_filename = filename.replace('\\', '/')
                                path_parts = normalized_filename.split('/')
                                rel_filename = path_parts[-1]  # The actual filename
                                rel_path = '/'.join(path_parts[:-1])  # The relative folder path
                                
                                # Create the folder structure
                                folder_path = os.path.join(full_target_path, rel_path)
                                if not os.path.exists(folder_path):
                                    try:
                                        os.makedirs(folder_path, exist_ok=True)
                                        print(f"Created folder structure: {folder_path}")
                                    except Exception as e:
                                        print(f"Error creating folder structure {folder_path}: {str(e)}")
                                        continue
                                
                                # Save the file in the correct folder
                                file_path = os.path.join(folder_path, rel_filename)
                            else:
                                # Regular file (not in a folder)
                                file_path = os.path.join(full_target_path, filename)
                            
                            # Save the file
                            try:
                                with open(file_path, 'wb') as f:
                                    f.write(item.file.read())
                                files_saved += 1
                                print(f"Successfully saved file: {filename} to {file_path}")
                            except Exception as e:
                                print(f"Error saving file {filename}: {str(e)}")
                                continue
                
                # Send response
                if files_saved > 0:
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Upload successful: {files_saved} files saved".encode())
                else:
                    self.send_error(400, "No valid files found in upload")
                
                return
            except Exception as e:
                print(f"Error handling file upload: {str(e)}")
                self.send_error(500, f"Server error: {str(e)}")
                return

if __name__ == "__main__":
    def kill_process_on_port(port):
        try:
            # Find process using the port
            cmd = f"lsof -i :{port} -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                print(f"Killing existing process {pid} on port {port}")
                subprocess.run(['kill', '-9', pid])
                return True
        except:
            pass
        return False
    
    parser = argparse.ArgumentParser(description='Start a simple HTTP file server')
    parser.add_argument('--port', type=int, default=80, help='Port to run the server on (default: 80)')
    parser.add_argument('--directory', type=str, default='.', help='Directory to serve files from (default: current directory)')
    
    args = parser.parse_args()
    
    # Kill any existing process on the port
    kill_process_on_port(args.port)
    
    # Create the directory if it doesn't exist
    os.makedirs(args.directory, exist_ok=True)
    
    # Create the server
    handler = partial(FixedHTTPRequestHandler, directory=args.directory)
    server = socketserver.TCPServer(("0.0.0.0", args.port), handler)
    
    print(f"Serving files from {os.path.abspath(args.directory)}")
    print(f"Server started at:")
    print(f"  Local: http://localhost:{args.port}/")
    print(f"  Network: http://{socket.gethostbyname(socket.gethostname())}:{args.port}/")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        try:
            server.shutdown()
            server.server_close()
        except:
            pass
        finally:
            # Force kill any remaining process on the port
            kill_process_on_port(args.port)
            # Force terminate the process
            os.kill(os.getpid(), signal.SIGKILL)
