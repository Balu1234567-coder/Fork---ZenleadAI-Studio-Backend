import google.generativeai as genai
from pylatex import Document, Section, Subsection, Command, NewPage, Package
from pylatex.utils import italic, bold, NoEscape
import os
import json
import subprocess
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyApdAVPzdAXf01b-xojrpUu3hUpVfPOFKc"
genai.configure(api_key=GEMINI_API_KEY)

@dataclass
class ResearchPaperConfig:
    topic: str
    research_question: str
    field: str
    research_type: str
    methodology: str
    paper_length: str
    citation_style: str
    academic_level: str
    target_venue: str
    depth_levels: Dict[str, int]
    authors: List[str]
    institution: str
    keywords: List[str]
    abstract_word_count: int
    email: str
    department: str
    country: str

class AIContentGenerator:
    """Advanced AI content generator with recursive prompt engineering"""
    
    def __init__(self, config: ResearchPaperConfig):
        self.config = config
        self.model = genai.GenerativeModel('gemini-pro')
        self.generated_content = {}
    
    async def generate_section_content(self, section_type: str, context: str = "", depth_level: int = 3) -> str:
        """Generate content for specific section with recursive depth"""
        
        section_prompts = {
            "abstract": self._create_abstract_prompt,
            "introduction": self._create_introduction_prompt,
            "literature_review": self._create_literature_review_prompt,
            "methodology": self._create_methodology_prompt,
            "results": self._create_results_prompt,
            "discussion": self._create_discussion_prompt,
            "conclusion": self._create_conclusion_prompt
        }
        
        if section_type not in section_prompts:
            raise ValueError(f"Unknown section: {section_type}")
        
        # Generate base content
        base_prompt = section_prompts[section_type](context, depth_level)
        
        try:
            response = await self.model.generate_content_async(base_prompt)
            base_content = response.text
            
            # Recursive enhancement based on depth level
            if depth_level >= 4:
                enhanced_content = await self._enhance_content(section_type, base_content, depth_level)
                return enhanced_content
            
            return base_content
            
        except Exception as e:
            print(f"Error generating {section_type}: {e}")
            return self._get_fallback_content(section_type)
    
    async def _enhance_content(self, section_type: str, base_content: str, depth_level: int) -> str:
        """Recursively enhance content with additional depth"""
        
        enhancement_prompt = f"""
        Enhance and expand the following {section_type} content for a {self.config.field} research paper.
        
        Original content:
        {base_content}
        
        Requirements:
        - Depth level: {depth_level}/5
        - Research field: {self.config.field}
        - Research type: {self.config.research_type}
        - Add more technical depth and academic rigor
        - Include relevant theoretical frameworks
        - Add specific examples and applications
        - Maintain academic writing style
        - Target audience: {self.config.academic_level} level
        
        Enhanced content:
        """
        
        try:
            response = await self.model.generate_content_async(enhancement_prompt)
            return response.text
        except Exception as e:
            print(f"Enhancement failed for {section_type}: {e}")
            return base_content
    
    def _create_abstract_prompt(self, context: str, depth: int) -> str:
        word_count = self.config.abstract_word_count
        return f"""
        Write a comprehensive academic abstract for a research paper with these specifications:
        
        Title: {self.config.topic}
        Research Question: {self.config.research_question}
        Field: {self.config.field}
        Research Type: {self.config.research_type}
        Methodology: {self.config.methodology}
        Keywords: {', '.join(self.config.keywords)}
        Target Venue: {self.config.target_venue}
        Academic Level: {self.config.academic_level}
        
        Requirements:
        - Exactly {word_count} words
        - Depth level: {depth}/5
        - Include: problem statement, methodology, key findings, significance
        - Use technical terminology appropriate for {self.config.field}
        - Target {self.config.target_venue} publication standards
        
        Context: {context}
        
        Write a compelling, precise abstract:
        """
    
    def _create_introduction_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a comprehensive introduction section for a {self.config.field} research paper.
        
        Paper Details:
        - Title: {self.config.topic}
        - Research Question: {self.config.research_question}
        - Research Type: {self.config.research_type}
        - Target: {self.config.target_venue}
        - Academic Level: {self.config.academic_level}
        
        Requirements:
        - Depth level: {depth}/5 (1=brief, 5=comprehensive)
        - Length: {800 + (depth * 200)} words approximately
        - Structure: Background → Problem → Gap → Objectives → Contributions → Paper Organization
        - Include relevant background in {self.config.field}
        - Establish the research problem clearly
        - Justify the importance and relevance
        - State research objectives and contributions
        - Include 3-5 preliminary citations (Author, Year format)
        
        Previous context: {context}
        
        Generate a well-structured introduction:
        """
    
    def _create_literature_review_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a comprehensive literature review for a {self.config.field} research paper on {self.config.topic}.
        
        Specifications:
        - Research Question: {self.config.research_question}
        - Keywords: {', '.join(self.config.keywords)}
        - Depth level: {depth}/5
        - Length: {1000 + (depth * 300)} words approximately
        
        Structure Requirements:
        1. Overview of research domain
        2. Theoretical foundations
        3. Key empirical studies
        4. Methodological approaches in the field
        5. Current trends and developments
        6. Research gaps and limitations
        7. Positioning of current work
        
        Include:
        - 8-12 realistic citations (Author et al., Year)
        - Critical analysis, not just summary
        - Clear identification of research gap
        - Connection to your research question
        - Theoretical frameworks relevant to {self.config.methodology}
        
        Previous sections: {context}
        
        Generate comprehensive literature review:
        """
    
    def _create_methodology_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a detailed methodology section for a {self.config.research_type} using {self.config.methodology}.
        
        Research Context:
        - Field: {self.config.field}
        - Question: {self.config.research_question}
        - Academic Level: {self.config.academic_level}
        - Depth: {depth}/5
        
        Required Components:
        1. Research Design and Approach
        2. Data Collection Methods
        3. Sample/Population (if applicable)
        4. Data Analysis Techniques
        5. Validity and Reliability Measures
        6. Ethical Considerations
        7. Limitations and Assumptions
        
        Specific to {self.config.methodology}:
        - Justify methodology choice
        - Detailed procedures
        - Quality assurance measures
        - Statistical analysis plan (if quantitative)
        - Theoretical framework application
        
        Length: {800 + (depth * 250)} words
        
        Previous content: {context}
        
        Generate rigorous methodology:
        """
    
    def _create_results_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a comprehensive results section for a {self.config.field} research paper.
        
        Study Details:
        - Research Type: {self.config.research_type}
        - Methodology: {self.config.methodology}
        - Research Question: {self.config.research_question}
        - Depth: {depth}/5
        
        Requirements:
        - Present findings objectively
        - Include statistical results (if applicable)
        - Reference figures/tables (e.g., "as shown in Figure 1")
        - Organize by research questions/hypotheses
        - Use appropriate statistical language
        - No interpretation (save for discussion)
        
        Structure:
        1. Overview of analysis
        2. Descriptive statistics/demographics
        3. Main findings by research question
        4. Additional/secondary findings
        5. Summary of key results
        
        Length: {600 + (depth * 200)} words
        
        Context: {context}
        
        Generate realistic results:
        """
    
    def _create_discussion_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a comprehensive discussion section for a {self.config.field} research paper.
        
        Paper Context:
        - Topic: {self.config.topic}
        - Research Question: {self.config.research_question}
        - Field: {self.config.field}
        - Depth: {depth}/5
        
        Structure Requirements:
        1. Summary of key findings
        2. Interpretation of results
        3. Comparison with existing literature
        4. Theoretical implications
        5. Practical applications
        6. Study limitations
        7. Future research directions
        
        Include:
        - Connection to literature review
        - Theoretical significance
        - Practical implications for {self.config.field}
        - Acknowledge limitations honestly
        - Suggest specific future research
        - Broader impact discussion
        
        Length: {800 + (depth * 300)} words
        
        All previous sections: {context}
        
        Generate insightful discussion:
        """
    
    def _create_conclusion_prompt(self, context: str, depth: int) -> str:
        return f"""
        Write a strong conclusion section for a {self.config.field} research paper.
        
        Paper Summary:
        - Title: {self.config.topic}
        - Research Question: {self.config.research_question}
        - Key Contributions: Based on previous sections
        - Depth: {depth}/5
        
        Requirements:
        1. Restate research objectives
        2. Summarize key findings
        3. Highlight main contributions
        4. Discuss broader implications
        5. Suggest future research
        6. Concluding statement
        
        Guidelines:
        - No new information
        - Concise but comprehensive
        - Forward-looking perspective
        - Strong closing statement
        - Length: {300 + (depth * 100)} words
        
        Full paper context: {context}
        
        Generate impactful conclusion:
        """
    
    def _get_fallback_content(self, section_type: str) -> str:
        """Fallback content if AI generation fails"""
        fallbacks = {
            "abstract": f"This {self.config.research_type.lower()} investigates {self.config.research_question.lower()} in the field of {self.config.field}. The research employs {self.config.methodology.lower()} to address key challenges in {self.config.topic.lower()}. Findings contribute to theoretical understanding and practical applications in the field.",
            
            "introduction": f"The field of {self.config.field} faces significant challenges related to {self.config.topic.lower()}. This research addresses the critical question: {self.config.research_question} Using {self.config.methodology.lower()}, we investigate key aspects and provide novel contributions to the field.",
            
            "literature_review": f"Previous research in {self.config.field} has established foundations for understanding {self.config.topic.lower()}. However, gaps remain in addressing {self.config.research_question.lower()}. This review synthesizes existing knowledge and identifies opportunities for advancement.",
            
            "methodology": f"This {self.config.research_type.lower()} employs {self.config.methodology.lower()} to investigate {self.config.research_question.lower()}. The methodology ensures rigorous investigation while maintaining scientific validity and reliability.",
            
            "results": f"Analysis reveals significant findings related to {self.config.research_question.lower()}. Results demonstrate important patterns and relationships that contribute to understanding in {self.config.field}.",
            
            "discussion": f"The findings provide important insights into {self.config.research_question.lower()}. Results have implications for both theory and practice in {self.config.field}, while acknowledging study limitations and future research directions.",
            
            "conclusion": f"This research successfully addressed {self.config.research_question.lower()} through rigorous {self.config.methodology.lower()}. The work contributes to {self.config.field} knowledge and provides foundations for future investigation."
        }
        return fallbacks.get(section_type, "Content to be generated.")
    
    async def generate_complete_paper_content(self) -> Dict[str, str]:
        """Generate all paper sections with progressive context building"""
        
        print("🤖 Generating AI-powered research content...")
        
        # Build context progressively
        full_context = f"Research Topic: {self.config.topic}\nResearch Question: {self.config.research_question}\nField: {self.config.field}"
        
        sections = ["abstract", "introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
        generated_content = {}
        
        for section in sections:
            print(f"  🔄 Generating {section}...")
            depth = self.config.depth_levels.get(section, 3)
            
            content = await self.generate_section_content(section, full_context, depth)
            generated_content[section] = content
            
            # Add to context for next sections
            full_context += f"\n\n{section.upper()}:\n{content[:500]}..."
            
            # Small delay to respect API limits
            await asyncio.sleep(1)
        
        print("  ✅ AI content generation complete!")
        return generated_content

class EnhancedLaTeXGenerator:
    """Enhanced LaTeX generator with proper PDF conversion"""
    
    def __init__(self, template_name: str, config: ResearchPaperConfig, content_source: str = "ai"):
        self.config = config
        self.template_name = template_name
        self.content_source = content_source
        self.templates = self._get_templates()
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        self.template_config = self.templates[template_name]
    
    def _get_templates(self) -> Dict:
        return {
            "ieee_conference": {
                "document_class": "IEEEtran",
                "class_options": ["conference"],
                "packages": ["cite", "amsmath", "amssymb", "graphicx", "url"],
                "two_column": True,
                "bibliography_style": "IEEEtran"
            },
            "ieee_journal": {
                "document_class": "IEEEtran", 
                "class_options": ["journal"],
                "packages": ["cite", "amsmath", "amssymb", "graphicx", "url"],
                "two_column": False,
                "bibliography_style": "IEEEtran"
            },
            "acm_article": {
                "document_class": "acmart",
                "class_options": ["sigconf"],
                "packages": ["amsmath", "amssymb", "graphicx", "booktabs"],
                "two_column": False,
                "bibliography_style": "ACM-Reference-Format"
            },
            "arxiv_preprint": {
                "document_class": "article",
                "class_options": ["11pt"],
                "packages": ["amsmath", "amssymb", "graphicx", "url", "hyperref"],
                "two_column": False,
                "bibliography_style": "plain"
            }
        }
    
    def create_document(self) -> Document:
        """Create LaTeX document with proper configuration"""
        
        doc = Document(
            documentclass=self.template_config["document_class"],
            document_options=self.template_config["class_options"],
            fontenc='T1',
            inputenc='utf8'
        )
        
        # Add packages
        for package in self.template_config["packages"]:
            doc.packages.append(Package(package))
        
        # Add geometry for better margins
        doc.packages.append(Package('geometry', options={'margin': '1in'}))
        
        return doc
    
    def add_title_and_authors(self, doc: Document):
        """Add title and author information"""
        
        doc.append(Command('title', self.config.topic))
        
        if self.template_config["document_class"] == "IEEEtran":
            authors_text = " and ".join(self.config.authors)
            doc.append(Command('author', NoEscape(
                f"\\IEEEauthorblockN{{{authors_text}}}\\\\"
                f"\\IEEEauthorblockA{{{self.config.institution}\\\\{self.config.email}}}"
            )))
        else:
            authors_text = ", ".join(self.config.authors)
            doc.append(Command('author', NoEscape(
                f"{authors_text}\\\\"
                f"{self.config.institution}\\\\"
                f"\\texttt{{{self.config.email}}}"
            )))
        
        doc.append(Command('date', datetime.now().strftime("%B %Y")))
        doc.append(Command('maketitle'))
    
    async def generate_with_ai_content(self, filename: str) -> str:
        """Generate paper with AI-generated content"""
        
        # Generate AI content
        ai_generator = AIContentGenerator(self.config)
        content = await ai_generator.generate_complete_paper_content()
        
        return self._create_latex_document(content, filename)
    
    def generate_with_user_content(self, user_content: Dict[str, str], filename: str) -> str:
        """Generate paper with user-provided content"""
        
        return self._create_latex_document(user_content, filename)
    
    def _create_latex_document(self, content: Dict[str, str], filename: str) -> str:
        """Create the actual LaTeX document"""
        
        doc = self.create_document()
        
        # Add title and authors
        self.add_title_and_authors(doc)
        
        # Add abstract
        doc.append(NoEscape('\\begin{abstract}'))
        doc.append(content.get('abstract', 'Abstract content here.'))
        doc.append(NoEscape('\\end{abstract}'))
        
        # Add keywords
        if self.config.keywords:
            if self.template_config["document_class"] == "IEEEtran":
                doc.append(NoEscape('\\begin{IEEEkeywords}'))
                doc.append(", ".join(self.config.keywords))
                doc.append(NoEscape('\\end{IEEEkeywords}'))
            else:
                doc.append(NoEscape(f"\\textbf{{Keywords:}} {', '.join(self.config.keywords)}"))
        
        doc.append(NoEscape('\\vspace{0.3cm}'))
        
        # Add sections
        sections = [
            ("Introduction", content.get('introduction', 'Introduction content here.')),
            ("Literature Review", content.get('literature_review', 'Literature review content here.')),
            ("Methodology", content.get('methodology', 'Methodology content here.')),
            ("Results", content.get('results', 'Results content here.')),
            ("Discussion", content.get('discussion', 'Discussion content here.')),
            ("Conclusion", content.get('conclusion', 'Conclusion content here.'))
        ]
        
        for title, text in sections:
            with doc.create(Section(title, numbering=True)):
                doc.append(text)
        
        # Add bibliography
        doc.append(NoEscape(f'\\bibliographystyle{{{self.template_config["bibliography_style"]}}}'))
        doc.append(NoEscape('\\bibliography{references}'))
        
        # Generate LaTeX file
        tex_filename = f"{filename}.tex"
        doc.generate_tex(filename)
        
        print(f"    ✅ LaTeX file generated: {tex_filename}")
        return tex_filename

def compile_latex_to_pdf(tex_filename: str, max_attempts: int = 3) -> Optional[str]:
    """Robust LaTeX to PDF compilation with error handling"""
    
    print(f"    🔄 Compiling {tex_filename} to PDF...")
    
    try:
        # Create a simple bibliography if it doesn't exist
        if not os.path.exists("references.bib"):
            create_sample_bibliography()
        
        # Run pdflatex multiple times for proper compilation
        for attempt in range(max_attempts):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', tex_filename],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if attempt == 0:
                # Run bibtex after first pdflatex
                bibtex_result = subprocess.run(
                    ['bibtex', tex_filename.replace('.tex', '.aux')],
                    capture_output=True,
                    text=True
                )
        
        # Check if PDF was created
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        
        if os.path.exists(pdf_filename):
            print(f"    ✅ PDF compiled successfully: {pdf_filename}")
            # Clean up auxiliary files
            cleanup_aux_files(tex_filename.replace('.tex', ''))
            return pdf_filename
        else:
            print(f"    ❌ PDF compilation failed - file not created")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"    ❌ Compilation timeout - process took too long")
        return None
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Compilation error: {e}")
        return None
    except FileNotFoundError:
        print(f"    ❌ pdflatex not found. Please install LaTeX:")
        print(f"      • macOS: brew install --cask mactex")
        print(f"      • Ubuntu: sudo apt-get install texlive-full")
        print(f"      • Windows: Download MiKTeX from miktex.org")
        return None

def cleanup_aux_files(base_filename: str):
    """Clean up auxiliary LaTeX files"""
    aux_extensions = ['.aux', '.log', '.bbl', '.blg', '.out', '.toc', '.lof', '.lot']
    
    for ext in aux_extensions:
        aux_file = f"{base_filename}{ext}"
        if os.path.exists(aux_file):
            try:
                os.remove(aux_file)
            except:
                pass

def create_sample_bibliography():
    """Create a comprehensive sample bibliography"""
    bib_content = """
@article{smith2023ai,
    title={Artificial Intelligence Applications in Modern Research},
    author={Smith, John A. and Anderson, Mary K. and Johnson, Robert L.},
    journal={Journal of Advanced Computing},
    volume={45},
    number={3},
    pages={123--145},
    year={2023},
    publisher={IEEE Computer Society}
}

@inproceedings{lee2024machine,
    title={Machine Learning Approaches for Scientific Discovery},
    author={Lee, Sarah J. and Brown, Michael D.},
    booktitle={Proceedings of the International Conference on Artificial Intelligence},
    pages={67--89},
    year={2024},
    organization={ACM}
}

@book{davis2023research,
    title={Research Methodology in the Digital Age: A Comprehensive Guide},
    author={Davis, Lisa M. and Wilson, David K.},
    year={2023},
    publisher={Academic Press},
    address={New York, NY}
}

@article{garcia2024analysis,
    title={Statistical Analysis Methods for Complex Data},
    author={Garcia, Ana R. and Martinez, Carlos E.},
    journal={Statistics and Computing},
    volume={34},
    number={2},
    pages={201--225},
    year={2024},
    publisher={Springer}
}

@inproceedings{thompson2023framework,
    title={A Novel Framework for Empirical Research},
    author={Thompson, Jennifer L. and Clark, Peter S.},
    booktitle={International Symposium on Research Methods},
    pages={145--162},
    year={2023},
    organization={IEEE}
}
"""
    
    with open("references.bib", "w") as f:
        f.write(bib_content)
    
    print("    📚 Sample bibliography created: references.bib")

def get_user_content_choice() -> str:
    """Ask user whether they want to provide content or use AI generation"""
    
    print("\n📝 CONTENT GENERATION OPTIONS")
    print("-" * 35)
    print("1. 🤖 AI-Generated Content (Recommended)")
    print("   • Automated content generation using advanced prompts")
    print("   • Recursive enhancement based on depth levels")
    print("   • Professional academic writing")
    
    print("\n2. ✍️  Manual Content Input")
    print("   • Provide your own content for each section")
    print("   • Full control over paper content")
    print("   • Option to input from file")
    
    while True:
        choice = input("\nChoose content generation method (1 or 2): ").strip()
        if choice in ["1", "2"]:
            return "ai" if choice == "1" else "manual"
        print("Please enter 1 or 2")

def collect_manual_content(config: ResearchPaperConfig) -> Dict[str, str]:
    """Collect content manually from user"""
    
    print("\n✍️  MANUAL CONTENT INPUT")
    print("-" * 30)
    print("Enter content for each section (press Enter twice when finished with each section):")
    
    sections = ["abstract", "introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
    content = {}
    
    for section in sections:
        print(f"\n📝 {section.replace('_', ' ').title()}:")
        lines = []
        empty_line_count = 0
        
        while empty_line_count < 2:
            line = input()
            if line == "":
                empty_line_count += 1
            else:
                empty_line_count = 0
                lines.append(line)
        
        content[section] = " ".join(lines)
        print(f"✅ {section} content saved ({len(content[section])} characters)")
    
    return content

async def main():
    """Enhanced main function with proper PDF generation and content options"""
    
    print("🚀 ENHANCED AI RESEARCH PAPER GENERATOR")
    print("=" * 60)
    print("📝 Advanced content generation + PDF compilation")
    
    try:
        # Sample configuration (you can expand this with full user input)
        config = ResearchPaperConfig(
            topic="Advanced Machine Learning Techniques for Healthcare Analytics",
            research_question="How can deep learning models improve diagnostic accuracy in medical imaging?",
            field="Computer Science",
            research_type="Empirical Research",
            methodology="Mixed Methods",
            paper_length="Standard Conference",
            citation_style="IEEE",
            academic_level="PhD",
            target_venue="Conference",
            depth_levels={"introduction": 4, "literature_review": 5, "methodology": 4, "results": 4, "discussion": 5},
            authors=["Dr. AI Researcher", "Research Assistant"],
            institution="Advanced AI Research Institute",
            keywords=["machine learning", "healthcare", "deep learning", "medical imaging", "diagnostic accuracy"],
            abstract_word_count=250,
            email="research@ai-institute.edu",
            department="Department of Computer Science",
            country="United States"
        )
        
        print(f"\n📋 RESEARCH CONFIGURATION")
        print(f"Title: {config.topic}")
        print(f"Field: {config.field}")
        print(f"Question: {config.research_question}")
        
        # Content generation choice
        content_choice = get_user_content_choice()
        
        # Template selection
        available_templates = ["ieee_conference", "ieee_journal", "acm_article", "arxiv_preprint"]
        print(f"\n📄 Available templates: {', '.join(available_templates)}")
        
        selected_templates = input("Enter templates (comma-separated) or 'all': ").strip().lower()
        if selected_templates == "all":
            templates_to_generate = available_templates
        else:
            templates_to_generate = [t.strip() for t in selected_templates.split(",") if t.strip() in available_templates]
        
        if not templates_to_generate:
            templates_to_generate = ["ieee_conference", "arxiv_preprint"]
        
        print(f"\n🔄 GENERATING PAPERS...")
        print(f"Templates: {', '.join(templates_to_generate)}")
        
        generated_files = []
        
        for template_name in templates_to_generate:
            try:
                print(f"\n📝 Generating {template_name}...")
                
                generator = EnhancedLaTeXGenerator(template_name, config, content_choice)
                
                if content_choice == "ai":
                    # AI-generated content
                    tex_file = await generator.generate_with_ai_content(f"{template_name}_paper")
                else:
                    # Manual content input
                    user_content = collect_manual_content(config)
                    tex_file = generator.generate_with_user_content(user_content, f"{template_name}_paper")
                
                generated_files.append(tex_file)
                
                # Compile to PDF
                pdf_file = compile_latex_to_pdf(tex_file)
                if pdf_file:
                    generated_files.append(pdf_file)
                
            except Exception as e:
                print(f"    ❌ Error with {template_name}: {e}")
        
        # Final summary
        print(f"\n🎉 GENERATION COMPLETE!")
        print("-" * 40)
        
        tex_files = [f for f in generated_files if f.endswith('.tex')]
        pdf_files = [f for f in generated_files if f.endswith('.pdf')]
        
        print(f"📊 Generated {len(tex_files)} LaTeX files")
        print(f"📄 Generated {len(pdf_files)} PDF files")
        
        print(f"\n📁 Generated Files:")
        for file in generated_files:
            if os.path.exists(file):
                size = os.path.getsize(file) / 1024  # KB
                print(f"  • {file} ({size:.1f} KB)")
        
        if pdf_files:
            print(f"\n✅ PDF files ready for use!")
        else:
            print(f"\n⚠️  No PDFs generated. Check LaTeX installation.")
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Generation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Install requirements:
    # pip install pylatex google-generativeai
    
    asyncio.run(main())
