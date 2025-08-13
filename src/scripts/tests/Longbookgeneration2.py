import os
import json
import time
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import google.generativeai as genai
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
import requests
from urllib.parse import urlparse
from PIL import Image
import io

# Install required packages
# pip install google-generativeai reportlab pillow requests

@dataclass
class BookSettings:
    """Enhanced class to hold all book configuration settings"""
    concept: str
    genre: str
    target_audience: str
    book_length: str
    tone: str
    complexity: str
    perspective: str
    chapters_count: int = 10
    sections_per_chapter: int = 6
    pages_per_section: int = 3
    include_toc: bool = True
    include_chapters: bool = True
    include_images: bool = True  # Now enabled by default
    include_bibliography: bool = True
    include_index: bool = False
    include_appendix: bool = False
    author_name: str = "AI Generated"
    book_title: str = ""

class ImageSearcher:
    """Class to handle Google Custom Search for images"""
    
    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    def search_images(self, query: str, num_results: int = 3) -> List[Dict]:
        """Search for images using Google Custom Search API"""
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
            
            response = requests.get(self.base_url, params=params)
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
            print(f"Error searching images for '{query}': {e}")
            return []
    
    def download_image(self, url: str, filename: str, max_size_mb: int = 5) -> Optional[str]:
        """Download and save an image from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check file size
            if len(response.content) > max_size_mb * 1024 * 1024:
                print(f"Image too large: {len(response.content) / (1024*1024):.1f}MB")
                return None
            
            # Verify it's an image
            try:
                img = Image.open(io.BytesIO(response.content))
                img.verify()
            except Exception:
                print(f"Invalid image format: {url}")
                return None
            
            # Save the image
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            return filename
            
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None

class EnhancedBookGeneratorWithImages:
    def __init__(self, genai_api_key: str, search_api_key: str, cse_id: str):
        """Initialize the book generator with Gemini API and Image Search"""
        genai.configure(api_key=genai_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.image_searcher = ImageSearcher(search_api_key, cse_id)
        self.book_data = {}
        self.images_folder = "book_images"
        
        # Create images folder
        os.makedirs(self.images_folder, exist_ok=True)
        
        # Configure generation parameters
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=8192,
            top_p=0.95
        )
    
    def get_user_inputs(self) -> BookSettings:
        """Interactive function to get all user inputs"""
        print("=" * 60)
        print("📚 WELCOME TO AI LONG BOOK GENERATOR WITH IMAGES")
        print("=" * 60)
        
        # Book concept
        print("\n🎯 STEP 1: Book Concept")
        concept = input("What book do you want to write? Describe your concept:\n> ")
        
        # Genre selection
        print("\n📖 STEP 2: Genre Selection")
        genres = [
            "Non-Fiction", "Fiction", "Educational", "Business", 
            "Self-Help", "Children's", "Biography", "Health & Wellness", 
            "Technology", "History"
        ]
        print("Available genres:")
        for i, genre in enumerate(genres, 1):
            print(f"{i}. {genre}")
        
        while True:
            try:
                genre_choice = int(input("Select genre (1-10): "))
                if 1 <= genre_choice <= 10:
                    selected_genre = genres[genre_choice - 1]
                    break
                else:
                    print("Please enter a number between 1-10")
            except ValueError:
                print("Please enter a valid number")
        
        # Target audience
        print("\n👥 STEP 3: Target Audience")
        audiences = [
            "General Audience", "Professionals", "Students", 
            "Children", "Seniors", "Beginners", "Advanced Users"
        ]
        print("Available target audiences:")
        for i, audience in enumerate(audiences, 1):
            print(f"{i}. {audience}")
        
        while True:
            try:
                audience_choice = int(input("Select target audience (1-7): "))
                if 1 <= audience_choice <= 7:
                    selected_audience = audiences[audience_choice - 1]
                    break
                else:
                    print("Please enter a number between 1-7")
            except ValueError:
                print("Please enter a valid number")
        
        # Book length
        print("\n📏 STEP 4: Book Length")
        lengths = [
            ("Short Book", "50-100 pages"),
            ("Standard Book", "150-250 pages"),
            ("Extended Book", "300-400 pages"),
            ("Epic Book", "500+ pages")
        ]
        print("Available book lengths:")
        for i, (length, desc) in enumerate(lengths, 1):
            print(f"{i}. {length} ({desc})")
        
        while True:
            try:
                length_choice = int(input("Select book length (1-4): "))
                if 1 <= length_choice <= 4:
                    selected_length = lengths[length_choice - 1][0]
                    break
                else:
                    print("Please enter a number between 1-4")
            except ValueError:
                print("Please enter a valid number")
        
        # Writing style
        print("\n✍️ STEP 5: Writing Style")
        tone = input("Describe your preferred tone (e.g., Professional, Conversational, Academic) [Academic]: ") or "Academic"
        complexity = input("Complexity level (Beginner/Intermediate/Advanced) [Intermediate]: ") or "Intermediate"
        perspective = input("Writing perspective (First person/Second person/Third person) [Third person]: ") or "Third person"
        
        # Book structure
        print("\n🏗️ STEP 6: Book Structure")
        while True:
            try:
                chapters_count = int(input("How many chapters do you want? (5-20): "))
                if 5 <= chapters_count <= 20:
                    break
                else:
                    print("Please enter a number between 5-20")
            except ValueError:
                print("Please enter a valid number")
        
        while True:
            try:
                sections_per_chapter = int(input("How many sections per chapter? (3-10): "))
                if 3 <= sections_per_chapter <= 10:
                    break
                else:
                    print("Please enter a number between 3-10")
            except ValueError:
                print("Please enter a valid number")
        
        while True:
            try:
                pages_per_section = int(input("How many pages per section? (1-8): "))
                if 1 <= pages_per_section <= 8:
                    break
                else:
                    print("Please enter a number between 1-8")
            except ValueError:
                print("Please enter a valid number")
        
        # Additional settings
        print("\n📋 STEP 7: Additional Features")
        include_toc = input("Include Table of Contents? (y/n) [y]: ").lower()
        include_toc = include_toc == 'y' if include_toc else True
        
        include_images = input("🖼️  Include relevant images? (y/n) [y]: ").lower()
        include_images = include_images == 'y' if include_images else True
        
        include_bibliography = input("Include Bibliography? (y/n) [y]: ").lower()
        include_bibliography = include_bibliography == 'y' if include_bibliography else True
        
        include_index = input("Include Index? (y/n) [n]: ").lower() == 'y'
        
        # Author and title
        print("\n👤 STEP 8: Book Details")
        author_name = input("Author name (or press Enter for 'AI Generated'): ") or "AI Generated"
        book_title = input("Book title (or press Enter to auto-generate): ")
        
        # Create and return settings
        settings = BookSettings(
            concept=concept,
            genre=selected_genre,
            target_audience=selected_audience,
            book_length=selected_length,
            tone=tone,
            complexity=complexity,
            perspective=perspective,
            chapters_count=chapters_count,
            sections_per_chapter=sections_per_chapter,
            pages_per_section=pages_per_section,
            include_toc=include_toc,
            include_images=include_images,
            include_bibliography=include_bibliography,
            include_index=include_index,
            author_name=author_name,
            book_title=book_title
        )
        
        # Display summary
        print("\n" + "=" * 60)
        print("📊 BOOK GENERATION SUMMARY")
        print("=" * 60)
        print(f"📖 Book: {book_title or 'To be auto-generated'}")
        print(f"👤 Author: {author_name}")
        print(f"🎯 Concept: {concept[:50]}...")
        print(f"📚 Genre: {selected_genre}")
        print(f"👥 Audience: {selected_audience}")
        print(f"📏 Length: {selected_length}")
        print(f"🏗️ Structure: {chapters_count} chapters, {sections_per_chapter} sections each")
        print(f"📄 Estimated pages: {chapters_count * sections_per_chapter * pages_per_section}")
        print(f"🖼️  Include Images: {'Yes' if include_images else 'No'}")
        print("=" * 60)
        
        confirm = input("\n⚠️  This will generate a COMPLETE book with ALL chapters and images. Continue? (y/n): ").lower()
        if confirm != 'y':
            print("Book generation cancelled.")
            exit()
        
        return settings
    
    def identify_image_needs(self, chapter_title: str, content: str) -> List[str]:
        """Use AI to identify what images would be helpful for the content"""
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
            response = self.model.generate_content(prompt)
            search_terms = []
            for line in response.text.strip().split('\n'):
                term = line.strip()
                if term and not term.startswith('#'):
                    search_terms.append(term)
            return search_terms[:3]  # Limit to 3 images per chapter
        except Exception as e:
            print(f"Error identifying image needs: {e}")
            return []
    
    def fetch_images_for_chapter(self, chapter_number: int, chapter_title: str, content: str) -> List[str]:
        """Fetch relevant images for a chapter"""
        if not self.book_data.get('settings', {}).include_images:
            return []
        
        print(f"🖼️  Searching for images for Chapter {chapter_number}...")
        
        # Get AI suggestions for image search terms
        search_terms = self.identify_image_needs(chapter_title, content)
        
        downloaded_images = []
        
        for i, search_term in enumerate(search_terms):
            print(f"   Searching for: {search_term}")
            
            # Search for images
            images = self.image_searcher.search_images(search_term, num_results=2)
            
            if images:
                # Try to download the first available image
                for j, img_info in enumerate(images):
                    filename = f"{self.images_folder}/chapter_{chapter_number}_{i+1}_{j+1}.jpg"
                    
                    if self.image_searcher.download_image(img_info['url'], filename):
                        downloaded_images.append({
                            'filename': filename,
                            'caption': search_term.title(),
                            'source': img_info.get('context', 'Unknown')
                        })
                        print(f"   ✅ Downloaded: {search_term}")
                        break
                else:
                    print(f"   ❌ Failed to download: {search_term}")
            
            # Small delay to respect API limits
            time.sleep(1)
        
        return downloaded_images
    
    def generate_book_structure(self, settings: BookSettings) -> Dict:
        """Generate the complete book structure"""
        # Auto-generate title if not provided
        if not settings.book_title:
            title_prompt = f"Generate ONE concise book title (maximum 50 characters) for: {settings.concept}. Genre: {settings.genre}. Return only the title, nothing else."
            try:
                title_response = self.model.generate_content(title_prompt)
                clean_title = title_response.text.strip().split('\n')[0].replace('"', '').replace('*', '').replace('#', '')
                clean_title = clean_title.replace('**', '').replace('*', '')
                settings.book_title = clean_title[:50]
            except:
                settings.book_title = f"{settings.concept} Guide"
        
        prompt = f"""
        Create a detailed structure for a {settings.book_length.lower()} titled "{settings.book_title}".
        
        Book Details:
        - Concept: {settings.concept}
        - Genre: {settings.genre}
        - Target Audience: {settings.target_audience}
        - Tone: {settings.tone}
        - Complexity: {settings.complexity}
        - Perspective: {settings.perspective}
        - Chapters: {settings.chapters_count}
        - Sections per chapter: {settings.sections_per_chapter}
        - Pages per section: {settings.pages_per_section}
        - Will include images: {settings.include_images}
        
        Generate {settings.chapters_count} comprehensive chapters. For each chapter, provide:
        1. Chapter Number and Title (format: "Chapter X: Title")
        2. Chapter Overview (3-4 sentences)
        3. List of {settings.sections_per_chapter} section titles
        4. Key learning outcomes
        5. Estimated word count for the chapter
        
        Ensure logical flow from introduction to conclusion, covering all aspects of: {settings.concept}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            self.book_data['structure'] = response.text
            self.book_data['settings'] = settings
            
            # Parse structure to extract chapter information
            self.parse_structure()
            
            return {'success': True, 'structure': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def parse_structure(self):
        """Parse the generated structure to extract chapter titles and sections"""
        if 'structure' not in self.book_data:
            return
        
        structure_text = self.book_data['structure']
        self.book_data['parsed_chapters'] = []
        
        # Simple parsing - look for chapter patterns
        lines = structure_text.split('\n')
        current_chapter = None
        
        for line in lines:
            line = line.strip()
            # Look for chapter titles
            if re.match(r'chapter\s+\d+', line.lower()) or 'Chapter' in line:
                if current_chapter:
                    self.book_data['parsed_chapters'].append(current_chapter)
                current_chapter = {
                    'title': line,
                    'sections': []
                }
            # Look for section titles (numbered lists, bullet points, etc.)
            elif current_chapter and (re.match(r'\d+\.', line) or line.startswith('-') or line.startswith('•')):
                section_title = re.sub(r'^\d+\.\s*|^[-•]\s*', '', line)
                if section_title:
                    current_chapter['sections'].append(section_title)
        
        if current_chapter:
            self.book_data['parsed_chapters'].append(current_chapter)
    
    def generate_all_chapters(self):
        """Generate content for ALL chapters with images"""
        settings = self.book_data.get('settings')
        parsed_chapters = self.book_data.get('parsed_chapters', [])
        
        print(f"\n🚀 Starting generation of ALL {len(parsed_chapters)} chapters with images...")
        print("⏳ This may take time due to content generation and image downloads...")
        
        if 'chapters' not in self.book_data:
            self.book_data['chapters'] = {}
        
        for i, chapter_info in enumerate(parsed_chapters, 1):
            print(f"\n📝 Generating Chapter {i}/{len(parsed_chapters)}: {chapter_info['title'][:50]}...")
            
            # If no sections were parsed, create default sections
            sections = chapter_info['sections'] if chapter_info['sections'] else [f"Section {j+1}" for j in range(settings.sections_per_chapter)]
            
            # Generate chapter content
            chapter_result = self.elaborate_chapter(i, chapter_info['title'], sections)
            
            if chapter_result['success']:
                print(f"✅ Chapter {i} content completed ({len(chapter_result['content'])} characters)")
                
                # Fetch images for this chapter if enabled
                if settings.include_images:
                    images = self.fetch_images_for_chapter(i, chapter_info['title'], chapter_result['content'])
                    self.book_data['chapters'][f'chapter_{i}']['images'] = images
                    print(f"🖼️  Added {len(images)} images to Chapter {i}")
                
            else:
                print(f"❌ Error in Chapter {i}: {chapter_result.get('error', 'Unknown error')}")
            
            # Add delay to respect API limits
            time.sleep(3)
            
            # Save progress periodically
            if i % 3 == 0:  # Save every 3 chapters
                self.save_progress(f"progress_with_images_after_chapter_{i}.json")
                print(f"💾 Progress saved after Chapter {i}")
        
        print(f"\n🎉 ALL {len(parsed_chapters)} chapters with images generated successfully!")
    
    def elaborate_chapter(self, chapter_number: int, chapter_title: str, sections_list: List[str]) -> Dict:
        """Elaborate a specific chapter with detailed content"""
        settings = self.book_data.get('settings')
        
        prompt = f"""
        Write detailed, comprehensive content for {chapter_title}
        
        Book Context: {settings.concept}
        Writing Style: {settings.tone}, {settings.complexity} level, {settings.perspective}
        Target Audience: {settings.target_audience}
        Pages per section: {settings.pages_per_section} (approximately 300 words per page)
        Images will be added: {settings.include_images}
        
        Create {len(sections_list)} detailed sections:
        {chr(10).join([f"{i+1}. {section}" for i, section in enumerate(sections_list)])}
        
        For each section, write approximately {settings.pages_per_section * 300} words including:
        - Clear section heading with markdown formatting (## Section Title)
        - Introduction paragraph
        - Main content with detailed explanations
        - Practical examples and applications
        - Code examples, diagrams, or technical details where relevant
        - [IMAGE PLACEHOLDER] markers where visual aids would be helpful
        - Summary or key takeaways
        - Smooth transition to next section
        
        Include [IMAGE PLACEHOLDER: description] markers in the text where images would enhance understanding.
        
        Ensure the content is:
        - Comprehensive and detailed
        - Appropriate for {settings.target_audience}
        - Written in {settings.tone} tone
        - Technically accurate and informative
        - Well-structured and easy to follow
        - Enhanced by visual elements
        
        Total target word count for this chapter: {len(sections_list) * settings.pages_per_section * 300} words
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            chapter_key = f'chapter_{chapter_number}'
            self.book_data['chapters'][chapter_key] = {
                'title': chapter_title,
                'content': response.text,
                'sections': sections_list,
                'images': []  # Will be populated later
            }
            return {'success': True, 'content': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_pdf_export(self, filename: str = None) -> bool:
        """Export the complete book with images to PDF"""
        try:
            settings = self.book_data.get('settings')
            if not filename:
                safe_title = "".join(c for c in settings.book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_title.replace(' ', '_')}_COMPLETE_WITH_IMAGES.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(filename, pagesize=A4, 
                                  topMargin=72, bottomMargin=72,
                                  leftMargin=72, rightMargin=72)
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
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
                alignment=1,  # Center alignment
                textColor=colors.grey
            )
            
            # Build PDF content
            story = []
            
            # Title page
            story.append(Paragraph(settings.book_title, title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"by {settings.author_name}", styles['Normal']))
            story.append(Spacer(1, 24))
            story.append(Paragraph(f"Genre: {settings.genre}", styles['Normal']))
            story.append(Paragraph(f"Target Audience: {settings.target_audience}", styles['Normal']))
            if settings.include_images:
                story.append(Paragraph("Enhanced with Images", styles['Normal']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(PageBreak())
            
            # Book overview
            story.append(Paragraph("Book Overview", chapter_style))
            story.append(Paragraph(f"<b>Concept:</b> {settings.concept}", body_style))
            story.append(Spacer(1, 12))
            
            # Book statistics
            total_pages = settings.chapters_count * settings.sections_per_chapter * settings.pages_per_section
            generated_chapters = len(self.book_data.get('chapters', {}))
            total_images = sum(len(chapter.get('images', [])) for chapter in self.book_data.get('chapters', {}).values())
            
            stats_data = [
                ['Statistic', 'Value'],
                ['Total Chapters', str(settings.chapters_count)],
                ['Generated Chapters', str(generated_chapters)],
                ['Sections per Chapter', str(settings.sections_per_chapter)],
                ['Pages per Section', str(settings.pages_per_section)],
                ['Estimated Total Pages', str(total_pages)],
                ['Total Images', str(total_images)],
                ['Writing Tone', settings.tone],
                ['Complexity Level', settings.complexity],
                ['Perspective', settings.perspective]
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
            
            story.append(stats_table)
            story.append(PageBreak())
            
            # Table of Contents
            if settings.include_toc:
                story.append(Paragraph("Table of Contents", chapter_style))
                if 'chapters' in self.book_data:
                    for chapter_key, chapter_data in self.book_data['chapters'].items():
                        chapter_num = chapter_key.split('_')[1]
                        story.append(Paragraph(f"Chapter {chapter_num}: {chapter_data['title']}", body_style))
                story.append(PageBreak())
            
            # Main content - ALL CHAPTERS WITH IMAGES
            if 'chapters' in self.book_data:
                for chapter_key, chapter_data in self.book_data['chapters'].items():
                    # Chapter title
                    story.append(Paragraph(chapter_data['title'], chapter_style))
                    story.append(Spacer(1, 12))
                    
                    # Chapter content with images
                    content_paragraphs = chapter_data['content'].split('\n')
                    images = chapter_data.get('images', [])
                    image_index = 0
                    
                    for paragraph in content_paragraphs:
                        if paragraph.strip():
                            # Check for section headings (markdown format)
                            if paragraph.strip().startswith('##'):
                                heading_text = paragraph.strip().replace('##', '').strip()
                                story.append(Paragraph(heading_text, section_style))
                                
                                # Add image after section heading if available
                                if image_index < len(images) and os.path.exists(images[image_index]['filename']):
                                    try:
                                        img = ReportLabImage(images[image_index]['filename'], width=4*inch, height=3*inch)
                                        story.append(Spacer(1, 6))
                                        story.append(img)
                                        story.append(Paragraph(f"Figure: {images[image_index]['caption']}", caption_style))
                                        story.append(Spacer(1, 6))
                                        image_index += 1
                                    except Exception as e:
                                        print(f"Error adding image: {e}")
                                
                            # Check for other headings
                            elif paragraph.strip().startswith('#'):
                                heading_text = paragraph.strip().replace('#', '').strip()
                                story.append(Paragraph(heading_text, section_style))
                            # Check for image placeholders
                            elif '[IMAGE PLACEHOLDER' in paragraph:
                                # Skip placeholder text, image already added
                                continue
                            # Regular paragraph
                            elif paragraph.strip():
                                story.append(Paragraph(paragraph.strip(), body_style))
                    
                    # Add any remaining images at the end of chapter
                    while image_index < len(images):
                        if os.path.exists(images[image_index]['filename']):
                            try:
                                img = ReportLabImage(images[image_index]['filename'], width=4*inch, height=3*inch)
                                story.append(Spacer(1, 6))
                                story.append(img)
                                story.append(Paragraph(f"Figure: {images[image_index]['caption']}", caption_style))
                            except Exception as e:
                                print(f"Error adding image: {e}")
                        image_index += 1
                    
                    story.append(PageBreak())
            
            # Bibliography (if enabled)
            if settings.include_bibliography:
                story.append(Paragraph("Bibliography & Image Sources", chapter_style))
                story.append(Paragraph("This book was generated using AI technology with images sourced from publicly available resources.", body_style))
                
                # List image sources
                if settings.include_images:
                    story.append(Paragraph("Image Sources:", section_style))
                    for chapter_key, chapter_data in self.book_data.get('chapters', {}).items():
                        for img in chapter_data.get('images', []):
                            story.append(Paragraph(f"• {img['caption']}: {img.get('source', 'Unknown source')}", body_style))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return False
    
    def save_progress(self, filename: str = "book_progress_with_images.json"):
        """Save current progress to JSON file"""
        try:
            book_data_copy = self.book_data.copy()
            if 'settings' in book_data_copy:
                settings_dict = {}
                settings_obj = book_data_copy['settings']
                for field in ['concept', 'genre', 'target_audience', 'book_length', 'tone', 
                             'complexity', 'perspective', 'chapters_count', 'sections_per_chapter', 
                             'pages_per_section', 'author_name', 'book_title', 'include_toc', 
                             'include_images', 'include_bibliography', 'include_index']:
                    settings_dict[field] = getattr(settings_obj, field)
                book_data_copy['settings'] = settings_dict
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(book_data_copy, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False

def main():
    """Interactive main function for complete book generation with images"""
    
    # API Keys
    GENAI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyApdAVPzdAXf01b-xojrpUu3hUpVfPOFKc"
    SEARCH_API_KEY = "AIzaSyDeu1TlQvvtapu9hBg-d9hDB-Mr_S7mx7k"
    CSE_ID = "a274cb56528ef4919"
    
    try:
        # Initialize generator
        generator = EnhancedBookGeneratorWithImages(GENAI_API_KEY, SEARCH_API_KEY, CSE_ID)
        
        # Get user inputs
        settings = generator.get_user_inputs()
        
        # Generate book structure
        print("\n🚀 Generating book structure...")
        structure_result = generator.generate_book_structure(settings)
        
        if structure_result['success']:
            print("✅ Book structure generated successfully!")
            print(f"\n📖 Book Title: {settings.book_title}")
            print(f"📊 Estimated Total Pages: {settings.chapters_count * settings.sections_per_chapter * settings.pages_per_section}")
            
            # Save initial progress
            generator.save_progress(f"{settings.book_title.replace(' ', '_')}_initial_progress.json")
            
            # Generate ALL chapters with images
            print(f"\n🚀 Now generating ALL {settings.chapters_count} chapters with images...")
            print("⚠️  This will take significant time due to content generation and image downloads!")
            
            start_time = time.time()
            generator.generate_all_chapters()
            end_time = time.time()
            
            print(f"\n🎉 Book generation completed in {end_time - start_time:.2f} seconds!")
            
            # Save complete progress
            generator.save_progress(f"{settings.book_title.replace(' ', '_')}_COMPLETE_WITH_IMAGES_progress.json")
            
            # Export to PDF with images
            print("\n📄 Exporting complete book with images to PDF...")
            pdf_success = generator.create_pdf_export()
            
            if pdf_success:
                print(f"✅ Complete PDF with images exported successfully!")
                pdf_name = f"{settings.book_title.replace(' ', '_')}_COMPLETE_WITH_IMAGES.pdf"
                print(f"📁 File saved as: {pdf_name}")
                
                # Show final statistics
                total_words = sum(len(chapter['content'].split()) for chapter in generator.book_data.get('chapters', {}).values())
                total_images = sum(len(chapter.get('images', [])) for chapter in generator.book_data.get('chapters', {}).values())
                
                print(f"\n📊 FINAL STATISTICS:")
                print(f"📖 Total Chapters Generated: {len(generator.book_data.get('chapters', {}))}")
                print(f"📝 Total Words: {total_words:,}")
                print(f"🖼️  Total Images: {total_images}")
                print(f"📄 Estimated Pages: {total_words // 300}")
                print(f"📁 Images saved in: {generator.images_folder}/")
                
            else:
                print("❌ Error creating PDF")
            
        else:
            print(f"❌ Error generating structure: {structure_result['error']}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Book generation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
