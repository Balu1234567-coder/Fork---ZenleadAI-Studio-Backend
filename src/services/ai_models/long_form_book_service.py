import os
import time
import asyncio
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
import google.generativeai as genai
from src.models.ai_models.long_form_book import *
from src.config.env import env_config
import logging
import json
from io import BytesIO
import requests
from PIL import Image

logger = logging.getLogger(__name__)

class ImageSearcher:
    """Enhanced image searcher based on your Longbookgeneration2.py"""
    
    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search_images(self, query: str, num_results: int = 3) -> List[Dict]:
        """Search for images using Google Custom Search API - Enhanced version"""
        try:
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'searchType': 'image',
                'num': min(num_results, 10),  # API limit is 10
                'safe': 'active',
                'imgSize': 'medium',
                'imgType': 'photo',
                'rights': 'cc_publicdomain,cc_attribute,cc_sharealike,cc_noncommercial,cc_nonderived'
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(self.base_url, params=params, timeout=10)
            )
            
            response.raise_for_status()
            data = response.json()
            
            images = []
            if 'items' in data:
                for item in data['items']:
                    images.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'thumbnail': item.get('image', {}).get('thumbnailLink', ''),
                        'context': item.get('image', {}).get('contextLink', ''),
                        'size': item.get('image', {}).get('byteSize', 0)
                    })
            
            return images
            
        except Exception as e:
            logger.error(f"Error searching images for '{query}': {e}")
            return []

    async def download_image_as_base64(self, url: str, max_size_mb: int = 5) -> Optional[str]:
        """Download image and return as base64 - Enhanced from your code"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=10)
            )
            
            response.raise_for_status()
            
            # Check file size
            if len(response.content) > max_size_mb * 1024 * 1024:
                logger.warning(f"Image too large: {len(response.content) / (1024*1024):.1f}MB")
                return None
            
            # Verify it's an image
            try:
                img = Image.open(BytesIO(response.content))
                img.verify()
                
                # Convert to base64
                img_base64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:image/jpeg;base64,{img_base64}"
                
            except Exception:
                logger.warning(f"Invalid image format: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

class LongFormBookService:
    """Enhanced service based on your fantastic Longbookgeneration2.py logic"""
    
    def __init__(self):
        genai.configure(api_key=env_config.GOOGLE_AI_STUDIO_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=8192,
            top_p=0.95
        )
        
        # Get image search credentials
        self.google_search_api_key = env_config.GOOGLE_SEARCH_API_KEY
        self.default_cse_id = env_config.IMAGE_RETRIEVE_CSE_ID


    async def generate_book_stream(self, request: LongFormBookRequest) -> AsyncGenerator[str, None]:
        """Generate complete book with streaming - Enhanced from your Longbookgeneration2.py"""
        start_time = time.time()
        
        try:
            # Stream initial metadata
            yield json.dumps({
                "type": "start",
                "message": f"🚀 Starting comprehensive book generation: '{request.book_title or 'Auto-generating title...'}'",
                "estimated_time": "15-30 minutes for complete book with images",
                "chapters_count": request.chapters_count,
                "include_images": request.include_images,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Step 1: Generate book structure (like your get_user_inputs + generate_book_structure)
            yield json.dumps({
                "type": "progress",
                "message": "📖 Creating detailed book structure and outline...",
                "progress": 5
            })
            
            structure = await self._generate_book_structure(request)
            
            yield json.dumps({
                "type": "structure",
                "message": f"✅ Book structure created: '{structure['title']}'",
                "data": {
                    "title": structure['title'],
                    "chapters_preview": structure['parsed_chapters'][:3],
                    "total_chapters": len(structure['parsed_chapters']),
                    "estimated_pages": len(structure['parsed_chapters']) * request.sections_per_chapter * request.pages_per_section
                }
            })

            # Step 2: Generate all chapters with images (like your generate_all_chapters)
            total_chapters = len(structure['parsed_chapters'])
            complete_book_data = {
                "book_metadata": {},
                "table_of_contents": [],
                "chapters": [],
                "all_images": []
            }

            for i, chapter_info in enumerate(structure['parsed_chapters'], 1):
                base_progress = 10 + (i / total_chapters) * 60  # 10-70% for chapters
                
                yield json.dumps({
                    "type": "progress",
                    "message": f"📝 Generating FULL Chapter {i}/{total_chapters}: {chapter_info['title'][:50]}...",
                    "progress": int(base_progress),
                    "current_chapter": i,
                    "total_chapters": total_chapters
                })

                # Generate chapter content (like your elaborate_chapter)
                chapter_result = await self._generate_full_chapter_content(request, chapter_info, i)
                
                # Add images if requested (like your fetch_images_for_chapter)
                chapter_images = []
                if request.include_images:
                    yield json.dumps({
                        "type": "progress",
                        "message": f"🖼️ Searching and adding images to Chapter {i}...",
                        "progress": int(base_progress + 5)
                    })
                    
                    chapter_images = await self._add_comprehensive_images(chapter_result)
                    
                    # Stream images as they're added
                    for img in chapter_images:
                        yield json.dumps({
                            "type": "image_added",
                            "chapter_number": i,
                            "image": {
                                "caption": img['caption'],
                                "data": img['data'][:100] + "..." if len(img['data']) > 100 else img['data'],  # Truncated for streaming
                                "source": img.get('source', 'Unknown'),
                                "size": len(img['data'])
                            }
                        })
                    
                    yield json.dumps({
                        "type": "progress",
                        "message": f"✅ Added {len(chapter_images)} images to Chapter {i}",
                        "progress": int(base_progress + 8)
                    })

                # Stream FULL chapter completion (not just preview!)
                yield json.dumps({
                    "type": "chapter_complete",
                    "chapter_number": i,
                    "title": chapter_result.title,
                    "full_content": chapter_result.content,  # FULL CONTENT, not preview!
                    "word_count": chapter_result.word_count,
                    "sections": chapter_result.sections,
                    "images": [
                        {
                            "caption": img['caption'],
                            "data": img['data'],
                            "source": img.get('source', 'AI Generated')
                        }
                        for img in chapter_images
                    ]
                })

                # Add to complete book data
                complete_book_data["chapters"].append({
                    "chapter_number": i,
                    "title": chapter_result.title,
                    "full_content": chapter_result.content,  # FULL CONTENT
                    "formatted_content": self._format_content_for_display(chapter_result.content),
                    "sections": chapter_result.sections,
                    "images": chapter_images,
                    "word_count": chapter_result.word_count
                })

                complete_book_data["all_images"].extend(chapter_images)

                # Small delay to respect API limits (from your code)
                await asyncio.sleep(2)

            # Step 3: Generate additional components (like your create_pdf_export logic)
            yield json.dumps({
                "type": "progress",
                "message": "📋 Creating comprehensive book metadata, TOC, and bibliography...",
                "progress": 75
            })

            toc = self._generate_comprehensive_toc(complete_book_data["chapters"])
            bibliography = self._generate_comprehensive_bibliography() if request.include_bibliography else None
            cover_info = self._generate_cover_info(request) if request.include_cover else None

            # Calculate metadata (like your statistics)
            total_words = sum(ch.get("word_count", 0) for ch in complete_book_data["chapters"])
            total_images = len(complete_book_data["all_images"])
            
            book_metadata = {
                "title": structure['title'],
                "author": request.author_name,
                "genre": request.genre.value,
                "target_audience": request.target_audience.value,
                "complexity": request.complexity.value,
                "tone": request.tone.value,
                "total_chapters": len(complete_book_data["chapters"]),
                "total_pages": total_words // 300,  # Like your estimation
                "total_words": total_words,
                "total_images": total_images,
                "generation_time": time.time() - start_time,
                "created_at": datetime.utcnow().isoformat(),
                "estimated_reading_time": total_words // 250  # Words per minute
            }

            complete_book_data.update({
                "book_metadata": book_metadata,
                "table_of_contents": toc,
                "bibliography": bibliography,
                "cover_design_info": cover_info
            })

            # Step 4: Generate PDF (like your create_pdf_export)
            yield json.dumps({
                "type": "progress",
                "message": "📄 Creating comprehensive PDF with all formatting and images...",
                "progress": 85
            })

            pdf_base64 = await self._generate_comprehensive_pdf(complete_book_data, request)

            # Final completion with full statistics
            yield json.dumps({
                "type": "complete",
                "message": f"🎉 Complete book with {total_images} images generated successfully!",
                "progress": 100,
                "book_data": {
                    "metadata": book_metadata,
                    "table_of_contents": toc,
                    "bibliography": bibliography,
                    "complete_chapters": complete_book_data["chapters"],  # FULL CHAPTERS
                    "pdf_base64": pdf_base64,
                    "full_book_data": complete_book_data,  # EVERYTHING for database
                    "generation_stats": {
                        "total_time_seconds": time.time() - start_time,
                        "words_per_minute": total_words / ((time.time() - start_time) / 60),
                        "images_per_chapter": total_images / len(complete_book_data["chapters"]) if complete_book_data["chapters"] else 0,
                        "average_chapter_words": total_words / len(complete_book_data["chapters"]) if complete_book_data["chapters"] else 0
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error generating book: {e}")
            yield json.dumps({
                "type": "error",
                "error_code": "GENERATION_ERROR",
                "message": f"Error generating book: {str(e)}",
                "error": str(e)
            })

    async def _generate_book_structure(self, request: LongFormBookRequest) -> Dict[str, Any]:
        """Generate book structure - Enhanced from your generate_book_structure method"""
        
        # Auto-generate title if not provided (exactly like your code)
        if not request.book_title:
            title_prompt = f"""
            Generate ONE concise book title (maximum 50 characters) for: {request.concept}
            Genre: {request.genre.value}
            Target Audience: {request.target_audience.value}
            Return only the title, nothing else.
            """
            
            try:
                title_response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(title_prompt)
                )
                clean_title = title_response.text.strip().split('\n')[0]
                clean_title = clean_title.replace('"', '').replace('*', '').replace('#', '')
                request.book_title = clean_title[:50]
            except:
                request.book_title = f"{request.concept} Guide"
        
        # Generate detailed structure (enhanced from your prompt)
        structure_prompt = f"""
        Create a detailed structure for a {request.book_length.value} book titled "{request.book_title}".

        Book Details:
        - Concept: {request.concept}
        - Genre: {request.genre.value}
        - Target Audience: {request.target_audience.value}
        - Tone: {request.tone.value}
        - Complexity: {request.complexity.value}
        - Perspective: {request.perspective.value}
        - Chapters: {request.chapters_count}
        - Sections per chapter: {request.sections_per_chapter}
        - Pages per section: {request.pages_per_section}
        - Will include images: {request.include_images}

        Generate {request.chapters_count} comprehensive chapters. For each chapter, provide:
        1. Chapter Number and Title (format: "Chapter X: Title")
        2. Chapter Overview (3-4 sentences)
        3. List of {request.sections_per_chapter} section titles
        4. Key learning outcomes
        5. Estimated word count for the chapter

        Ensure logical flow from introduction to conclusion, covering all aspects of: {request.concept}
        Make it comprehensive and suitable for {request.target_audience.value}.
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.generate_content(structure_prompt, generation_config=self.generation_config)
        )
        
        return {
            'title': request.book_title,
            'structure_text': response.text,
            'parsed_chapters': self._parse_structure(response.text, request.chapters_count)
        }

    def _parse_structure(self, structure_text: str, expected_chapters: int) -> List[Dict]:
        """Parse structure - Enhanced from your parse_structure method"""
        chapters = []
        lines = structure_text.split('\n')
        current_chapter = None
        
        for line in lines:
            line = line.strip()
            
            # Look for chapter titles (enhanced pattern matching)
            if ('chapter' in line.lower() and any(str(i) in line for i in range(1, expected_chapters + 1))) or \
               line.startswith('Chapter '):
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    'title': line,
                    'sections': []
                }
            
            # Look for section titles (enhanced patterns)
            elif current_chapter and (line.startswith('-') or line.startswith('•') or 
                                    line.startswith('*') or
                                    any(line.startswith(f"{i}.") for i in range(1, 20))):
                section_title = line.lstrip('-•*').lstrip('0123456789. ').strip()
                if section_title and len(section_title) > 3:  # Filter out very short sections
                    current_chapter['sections'].append(section_title)
        
        if current_chapter:
            chapters.append(current_chapter)
        
        # Fill missing sections if needed (like your code)
        for chapter in chapters:
            while len(chapter['sections']) < 3:
                chapter['sections'].append(f"Additional Section {len(chapter['sections']) + 1}")
        
        return chapters

    async def _generate_full_chapter_content(self, request: LongFormBookRequest, chapter_info: Dict, chapter_num: int) -> BookChapter:
        """Generate FULL detailed chapter content like your elaborate_chapter method"""
        
        sections = chapter_info.get('sections', [f"Section {i+1}" for i in range(request.sections_per_chapter)])
        
        # Enhanced prompt matching your Longbookgeneration2.py quality
        content_prompt = f"""
        Write comprehensive, detailed content for {chapter_info['title']}

        Book Context: {request.concept}
        Writing Style: {request.tone.value}, {request.complexity.value} level, {request.perspective.value}
        Target Audience: {request.target_audience.value}
        Pages per section: {request.pages_per_section} (300 words per page)

        Create {len(sections)} comprehensive sections:
        {chr(10).join([f"{i+1}. {section}" for i, section in enumerate(sections)])}

        For each section, write {request.pages_per_section * 300} words including:
        - Clear section heading with markdown formatting (## Section Title)
        - Detailed introduction paragraph
        - Comprehensive main content with detailed explanations
        - Practical examples and applications
        - Code examples, diagrams, or technical details where relevant
        - Case studies and real-world scenarios
        - Key insights and professional analysis
        - [IMAGE_SUGGESTION: description] markers where visual aids would be helpful
        - Summary or key takeaways
        - Smooth transition to next section

        Formatting requirements:
        - Use proper markdown headers (##, ###)
        - Include bullet points and numbered lists where appropriate
        - Add emphasis with **bold** and *italics*
        - Include code blocks or technical examples if relevant
        - Ensure professional, comprehensive content suitable for {request.target_audience.value}

        Ensure the content is:
        - Comprehensive and detailed
        - Appropriate for {request.target_audience.value}
        - Written in {request.tone.value} tone
        - Technically accurate and informative
        - Well-structured and easy to follow
        - Enhanced by visual elements

        Total target word count for this chapter: {len(sections) * request.pages_per_section * 300} words minimum
        Make this chapter comprehensive, detailed, and valuable to readers.
        """
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.generate_content(content_prompt, generation_config=self.generation_config)
        )
        
        content = response.text
        word_count = len(content.split())
        
        return BookChapter(
            chapter_number=chapter_num,
            title=chapter_info['title'],
            content=content,
            sections=sections,
            word_count=word_count
        )

    async def _add_comprehensive_images(self, chapter_result: BookChapter) -> List[Dict[str, Any]]:
        """Add images to chapter - Enhanced from your fetch_images_for_chapter method"""
        
        # Use environment credentials only
        search_api_key = self.google_search_api_key
        cse_id = self.default_cse_id
        
        images = []
        
        # Skip if no credentials available
        if not search_api_key or not cse_id:
            logger.info("No image search credentials available, skipping image generation")
            return images
        
        # Create ImageSearcher
        image_searcher = ImageSearcher(search_api_key, cse_id)
        
        # Use AI to identify image needs (like your identify_image_needs method)
        image_suggestions = await self._identify_image_needs(chapter_result.title, chapter_result.content)
        
        # Limit to 3 images per chapter (like your code)
        for suggestion in image_suggestions[:3]:
            try:
                search_results = await image_searcher.search_images(suggestion, num_results=2)
                
                if search_results:
                    for search_result in search_results:
                        img_data = await image_searcher.download_image_as_base64(search_result['url'])
                        if img_data:
                            images.append({
                                'caption': suggestion.title(),
                                'data': img_data,
                                'source': search_result.get('context', 'Unknown')
                            })
                            break  # Got one image for this suggestion
                
                # Small delay to respect API limits (from your code)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing image for '{suggestion}': {e}")
                continue
        
        return images

    async def _identify_image_needs(self, chapter_title: str, content: str) -> List[str]:
        """Use AI to identify image needs - From your identify_image_needs method"""
        prompt = f"""
        Analyze this chapter content and suggest 2-3 specific image search queries that would enhance understanding.

        Chapter: {chapter_title}
        Content preview: {content[:500]}...

        Provide specific, searchable terms for images that would be:
        1. Educational and relevant
        2. Appropriate for the content
        3. Safe for work
        4. Technically accurate

        Return only the search terms, one per line, maximum 3 terms.
        Example format:
        computer network diagram
        operating system architecture
        database schema example
        """

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            search_terms = []
            for line in response.text.strip().split('\n'):
                term = line.strip()
                if term and not term.startswith('#') and len(term) > 5:
                    search_terms.append(term)
            return search_terms[:3]
        except Exception as e:
            logger.error(f"Error identifying image needs: {e}")
            return []

    def _format_content_for_display(self, content: str) -> str:
        """Format content for HTML display"""
        # Convert markdown to HTML-like formatting
        formatted = content
        
        # Headers
        formatted = formatted.replace('### ', '<h3>').replace('\n### ', '</h3>\n<h3>')
        formatted = formatted.replace('## ', '<h2>').replace('\n## ', '</h2>\n<h2>')
        formatted = formatted.replace('# ', '<h1>').replace('\n# ', '</h1>\n<h1>')
        
        # Bold and italic
        formatted = formatted.replace('**', '<strong>').replace('**', '</strong>')
        formatted = formatted.replace('*', '<em>').replace('*', '</em>')
        
        # Paragraphs
        formatted = formatted.replace('\n\n', '</p>\n\n<p>')
        formatted = f'<p>{formatted}</p>'
        
        # Lists
        lines = formatted.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('• '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        return '\n'.join(result_lines)

    def _generate_comprehensive_toc(self, chapters: List[Dict]) -> List[Dict[str, str]]:
        """Generate TOC - Enhanced from your code"""
        toc = []
        for chapter in chapters:
            toc.append({
                'chapter_number': str(chapter["chapter_number"]),
                'title': chapter["title"],
                'page': str((chapter["chapter_number"] - 1) * 10 + 1),
                'word_count': str(chapter.get("word_count", 0)),
                'sections_count': str(len(chapter.get("sections", [])))
            })
        return toc

    def _generate_comprehensive_bibliography(self) -> List[str]:
        """Generate bibliography - Enhanced"""
        return [
            "AI Generated Content - Powered by Google Gemini",
            "Images sourced from Creative Commons licensed materials via Google Custom Search",
            "Generated using advanced natural language processing and machine learning",
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        ]

    def _generate_cover_info(self, request: LongFormBookRequest) -> Dict[str, Any]:
        """Generate cover info - Enhanced"""
        return {
            'title': request.book_title,
            'author': request.author_name,
            'genre': request.genre.value,
            'target_audience': request.target_audience.value,
            'style': 'modern',
            'color_scheme': 'professional',
            'design_elements': ['typography', 'gradient_background', 'subtle_graphics'],
            'estimated_pages': request.chapters_count * request.sections_per_chapter * request.pages_per_section
        }

    async def _generate_comprehensive_pdf(self, book_data: Dict, request: LongFormBookRequest) -> str:
        """Generate PDF with images - Enhanced from your create_pdf_export method"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import Image as ReportLabImage
            from io import BytesIO
            
            # Create PDF in memory
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                   topMargin=72, bottomMargin=72,
                                   leftMargin=72, rightMargin=72)
            
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles (from your code)
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,
                textColor=colors.darkblue
            )
            
            chapter_style = ParagraphStyle(
                'ChapterTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                spaceBefore=24,
                textColor=colors.darkred
            )
            
            section_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=6,
                spaceBefore=12,
                textColor=colors.darkgreen
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                alignment=0,
                leading=14
            )
            
            caption_style = ParagraphStyle(
                'ImageCaption',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=12,
                alignment=1,
                textColor=colors.grey
            )
            
            # Title page with full details (enhanced from your code)
            story.append(Paragraph(book_data["book_metadata"]["title"], title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"by {request.author_name}", styles['Normal']))
            story.append(Spacer(1, 24))
            story.append(Paragraph(f"Genre: {request.genre.value}", styles['Normal']))
            story.append(Paragraph(f"Target Audience: {request.target_audience.value}", styles['Normal']))
            story.append(Paragraph("Enhanced with AI-Generated Images", styles['Normal']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            
            # Book statistics (enhanced from your stats_table)
            stats_data = [
                ['Statistic', 'Value'],
                ['Total Chapters', str(book_data["book_metadata"]["total_chapters"])],
                ['Total Words', f"{book_data['book_metadata']['total_words']:,}"],
                ['Total Images', str(book_data["book_metadata"]["total_images"])],
                ['Estimated Pages', str(book_data["book_metadata"]["total_pages"])],
                ['Writing Tone', request.tone.value],
                ['Complexity Level', request.complexity.value],
                ['Target Audience', request.target_audience.value],
                ['Generation Time', f"{book_data['book_metadata']['generation_time']:.1f} seconds"]
            ]
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Spacer(1, 24))
            story.append(stats_table)
            story.append(PageBreak())
            
            # Table of contents (if enabled)
            if request.include_toc:
                story.append(Paragraph("Table of Contents", chapter_style))
                for item in book_data["table_of_contents"]:
                    story.append(Paragraph(f"Chapter {item['chapter_number']}: {item['title']}", body_style))
                story.append(PageBreak())
            
            # Main content - ALL CHAPTERS WITH IMAGES (enhanced from your code)
            for chapter in book_data["chapters"]:
                # Chapter title
                story.append(Paragraph(chapter["title"], chapter_style))
                story.append(Spacer(1, 12))
                
                # Chapter content with images
                content_paragraphs = chapter["full_content"].split('\n')
                images = chapter.get("images", [])
                image_index = 0
                
                for paragraph in content_paragraphs:
                    if paragraph.strip():
                        # Section headings
                        if paragraph.strip().startswith('##'):
                            heading_text = paragraph.strip().replace('##', '').strip()
                            story.append(Paragraph(heading_text, section_style))
                            
                            # Add image after section heading if available
                            if image_index < len(images):
                                img_data = images[image_index]
                                if img_data.get("data") and img_data["data"].startswith("data:image"):
                                    try:
                                        # Decode base64 image
                                        image_data = img_data["data"].split(",")[1]
                                        image_bytes = base64.b64decode(image_data)
                                        img_buffer = BytesIO(image_bytes)
                                        
                                        # Add image to PDF
                                        img = ReportLabImage(img_buffer, width=4*inch, height=3*inch)
                                        story.append(Spacer(1, 6))
                                        story.append(img)
                                        story.append(Paragraph(f"Figure: {img_data['caption']}", caption_style))
                                        story.append(Spacer(1, 6))
                                        image_index += 1
                                    except Exception as e:
                                        logger.error(f"Error adding image to PDF: {e}")
                        
                        # Regular paragraph
                        elif not '[IMAGE_SUGGESTION' in paragraph and not paragraph.strip().startswith('#'):
                            story.append(Paragraph(paragraph.strip(), body_style))
                
                story.append(PageBreak())
            
            # Bibliography (if enabled)
            if request.include_bibliography and book_data.get("bibliography"):
                story.append(Paragraph("Bibliography & Image Sources", chapter_style))
                for bib_item in book_data["bibliography"]:
                    story.append(Paragraph(f"• {bib_item}", body_style))
                
                # Add image sources
                if book_data.get("all_images"):
                    story.append(Paragraph("Image Sources:", section_style))
                    for img in book_data["all_images"]:
                        story.append(Paragraph(f"• {img['caption']}: {img.get('source', 'AI Generated')}", body_style))
            
            # Build PDF
            doc.build(story)
            
            # Convert to base64
            pdf_buffer.seek(0)
            pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            
            return pdf_base64
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return ""
