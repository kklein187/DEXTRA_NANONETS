"""URL processor for handling web pages and file downloads."""

import os
import re
import tempfile
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, NetworkError


class URLProcessor(BaseProcessor):
    """Processor for URLs and web pages."""
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check (or URL)
            
        Returns:
            True if this processor can handle the file
        """
        # Check if it looks like a URL
        return self._is_url(file_path)
    
    def process(self, file_path: str) -> ConversionResult:
        """Process the URL and return a conversion result.
        
        Args:
            file_path: URL to process
            
        Returns:
            ConversionResult containing the processed content
            
        Raises:
            NetworkError: If network operations fail
            ConversionError: If processing fails
        """
        try:
            import requests
            
            # First, check if this URL points to a file
            file_info = self._detect_file_from_url(file_path)
            
            if file_info:
                # This is a file URL, download and process it
                return self._process_file_url(file_path, file_info)
            else:
                # This is a web page, process it as HTML
                return self._process_web_page(file_path)
                
        except ImportError:
            raise ConversionError("requests and beautifulsoup4 are required for URL processing. Install them with: pip install requests beautifulsoup4")
        except requests.RequestException as e:
            raise NetworkError(f"Failed to fetch URL {file_path}: {str(e)}")
        except Exception as e:
            if isinstance(e, (NetworkError, ConversionError)):
                raise
            raise ConversionError(f"Failed to process URL {file_path}: {str(e)}")
    
    def _detect_file_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Detect if a URL points to a file and return file information.
        
        Args:
            url: URL to check
            
        Returns:
            File info dict if it's a file URL, None otherwise
        """
        try:
            import requests
            
            # Check URL path for file extensions
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            # Common file extensions
            file_extensions = {
                '.pdf': 'pdf',
                '.doc': 'doc',
                '.docx': 'docx',
                '.txt': 'txt',
                '.md': 'markdown',
                '.html': 'html',
                '.htm': 'html',
                '.xlsx': 'xlsx',
                '.xls': 'xls',
                '.csv': 'csv',
                '.ppt': 'ppt',
                '.pptx': 'pptx',
                '.jpg': 'image',
                '.jpeg': 'image',
                '.png': 'image',
                '.gif': 'image',
                '.bmp': 'image',
                '.tiff': 'image',
                '.tif': 'image',
                '.webp': 'image'
            }
            
            # Check for file extension in URL path
            for ext, file_type in file_extensions.items():
                if path.endswith(ext):
                    return {
                        'file_type': file_type,
                        'extension': ext,
                        'filename': os.path.basename(path) or f"downloaded_file{ext}"
                    }
            
            # If no extension in URL, check content-type header
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # Make a HEAD request to check content-type
                response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Check for file content types
                    if 'application/pdf' in content_type:
                        return {'file_type': 'pdf', 'extension': '.pdf', 'filename': 'downloaded_file.pdf'}
                    elif 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                        ext = '.docx' if 'openxmlformats' in content_type else '.doc'
                        return {'file_type': 'doc' if ext == '.doc' else 'docx', 'extension': ext, 'filename': f'downloaded_file{ext}'}
                    elif 'application/vnd.ms-excel' in content_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                        ext = '.xlsx' if 'openxmlformats' in content_type else '.xls'
                        return {'file_type': 'xlsx' if ext == '.xlsx' else 'xls', 'extension': ext, 'filename': f'downloaded_file{ext}'}
                    elif 'application/vnd.ms-powerpoint' in content_type or 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type:
                        ext = '.pptx' if 'openxmlformats' in content_type else '.ppt'
                        return {'file_type': 'pptx' if ext == '.pptx' else 'ppt', 'extension': ext, 'filename': f'downloaded_file{ext}'}
                    elif 'text/plain' in content_type:
                        return {'file_type': 'txt', 'extension': '.txt', 'filename': 'downloaded_file.txt'}
                    elif 'text/markdown' in content_type:
                        return {'file_type': 'markdown', 'extension': '.md', 'filename': 'downloaded_file.md'}
                    elif 'text/html' in content_type:
                        # HTML could be a web page or a file, check if it's likely a file
                        if 'attachment' in response.headers.get('content-disposition', '').lower():
                            return {'file_type': 'html', 'extension': '.html', 'filename': 'downloaded_file.html'}
                        # If it's HTML but not an attachment, treat as web page
                        return None
                    elif any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp']):
                        # Determine extension from content type
                        ext_map = {
                            'image/jpeg': '.jpg',
                            'image/png': '.png',
                            'image/gif': '.gif',
                            'image/bmp': '.bmp',
                            'image/tiff': '.tiff',
                            'image/webp': '.webp'
                        }
                        ext = ext_map.get(content_type, '.jpg')
                        return {'file_type': 'image', 'extension': ext, 'filename': f'downloaded_file{ext}'}
                        
            except requests.RequestException:
                # If HEAD request fails, assume it's a web page
                pass
                
        except Exception:
            pass
            
        return None
    
    def _process_file_url(self, url: str, file_info: Dict[str, Any]) -> ConversionResult:
        """Download and process a file from URL.
        
        Args:
            url: URL to download from
            file_info: Information about the file
            
        Returns:
            ConversionResult containing the processed content
        """
        try:
            import requests
            from ..extractor import DocumentExtractor
            
            # Download the file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_info['extension']) as temp_file:
                # Write the downloaded content and track size
                content_length = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        temp_file.write(chunk)
                        content_length += len(chunk)
                
                temp_file_path = temp_file.name
            
            try:
                # Process the downloaded file using the appropriate processor
                extractor = DocumentExtractor()
                result = extractor.extract(temp_file_path)
                
                # Add URL metadata to the result
                result.metadata.update({
                    "source_url": url,
                    "downloaded_filename": file_info['filename'],
                    "content_type": response.headers.get('content-type', ''),
                    "content_length": content_length
                })
                
                return result
                
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            raise ConversionError(f"Failed to download and process file from URL {url}: {str(e)}")
    
    def _process_web_page(self, url: str) -> ConversionResult:
        """Process a web page URL.
        
        Args:
            url: URL to process
            
        Returns:
            ConversionResult containing the processed content
        """
        try:
            from bs4 import BeautifulSoup
            import requests
            
            # Fetch the web page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            content_parts = []
            
            # Get title
            title = soup.find('title')
            if title:
                content_parts.append(f"# {title.get_text().strip()}\n")
            
            # Get main content
            main_content = self._extract_main_content(soup)
            if main_content:
                content_parts.append(main_content)
            else:
                # Fallback to body text
                body = soup.find('body')
                if body:
                    content_parts.append(body.get_text())
            
            content = '\n'.join(content_parts)
            
            # Clean up the content
            content = self._clean_content(content)
            
            metadata = {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content),
                "processor": self.__class__.__name__
            }
            
            return ConversionResult(content, metadata)
            
        except Exception as e:
            raise ConversionError(f"Failed to process web page {url}: {str(e)}")
    
    def _is_url(self, text: str) -> bool:
        """Check if the text looks like a URL.
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like a URL
        """
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_main_content(self, soup) -> str:
        """Extract main content from the HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted main content
        """
        # Try to find main content areas
        main_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '#content',
            'article',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text()
        
        # If no main content found, return empty string
        return ""
    
    def _clean_content(self, content: str) -> str:
        """Clean up the extracted web content.
        
        Args:
            content: Raw web text content
            
        Returns:
            Cleaned text content
        """
        # Remove excessive whitespace and normalize
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive whitespace
            line = ' '.join(line.split())
            if line.strip():
                cleaned_lines.append(line)
        
        # Join lines and add proper spacing
        content = '\n'.join(cleaned_lines)
        
        # Add spacing around headers
        content = content.replace('# ', '\n# ')
        content = content.replace('## ', '\n## ')
        
        return content.strip() 