import yaml
import re
import argparse
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

class ResumeOptimizer:
    def __init__(self, skills_config_path: str = None):
        # Load your validated skills from config
        self.validated_skills = self.load_validated_skills(skills_config_path)
        
        self.tech_keywords = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'kotlin', 'scala', 'ruby', 'php',
            
            # Frameworks & Libraries
            'react', 'vue', 'angular', 'node.js', 'nodejs', 'express', 'django', 'flask', 'spring', 'springboot',
            
            # Cloud & Infrastructure
            'aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'k8s', 'docker', 'containers', 'terraform', 'ansible',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'sqlite',
            
            # DevOps & CI/CD
            'jenkins', 'github actions', 'gitlab ci', 'ci/cd', 'cicd', 'devops', 'monitoring', 'prometheus', 'grafana',
            
            # Build Systems & Tools
            'bazel', 'gradle', 'maven', 'webpack', 'git', 'jira', 'confluence',
            
            # Methodologies
            'agile', 'scrum', 'microservices', 'rest api', 'graphql', 'tdd', 'unit testing',
            
            # AI/ML
            'machine learning', 'ai', 'tensorflow', 'pytorch', 'data science', 'nlp', 'computer vision'
        }
    
    def load_validated_skills(self, config_path: str = None) -> Dict:
        """Load validated skills configuration"""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            except Exception as e:
                print(f"Error loading skills config: {e}")
        
        # Return default empty config if file doesn't exist
        return {
            'expert': [],           # Technologies you're expert in
            'proficient': [],       # Technologies you're proficient with
            'familiar': [],         # Technologies you're familiar with
            'learning': [],         # Technologies you're currently learning
            'never_add': []         # Technologies to never add automatically
        }
    
    def validate_keyword(self, keyword: str, skill_level: str = 'familiar') -> bool:
        """Check if a keyword is safe to add based on your skill level"""
        keyword_lower = keyword.lower()
        
        # Never add these technologies
        if keyword_lower in [skill.lower() for skill in self.validated_skills.get('never_add', [])]:
            return False
        
        # Check if it's in your validated skills at the required level or higher
        skill_hierarchy = ['learning', 'familiar', 'proficient', 'expert']
        min_level_index = skill_hierarchy.index(skill_level)
        
        for level in skill_hierarchy[min_level_index:]:
            if keyword_lower in [skill.lower() for skill in self.validated_skills.get(level, [])]:
                return True
        
        return False
    
    def filter_safe_keywords(self, keywords: Dict[str, int]) -> Dict[str, int]:
        """Filter keywords to only include ones you can defend"""
        safe_keywords = {}
        unsafe_keywords = []
        
        for keyword, count in keywords.items():
            if self.validate_keyword(keyword, 'familiar'):
                safe_keywords[keyword] = count
            else:
                unsafe_keywords.append(keyword)
        
        if unsafe_keywords:
            print(f"\n⚠️  Skipping keywords you haven't validated:")
            for kw in unsafe_keywords:
                print(f"   - {kw}")
            print(f"   Add them to your skills config if you want to include them.\n")
        
        return safe_keywords
    
    def load_resume(self, yaml_path: str) -> Dict:
        """Load resume YAML file"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading resume: {e}")
            return {}
    
    def load_job_posting(self, job_path: str) -> str:
        """Load job posting text file"""
        try:
            with open(job_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading job posting: {e}")
            return ""
    
    def extract_keywords(self, job_text: str) -> Dict[str, int]:
        """Extract and count technical keywords from job posting"""
        # Clean and normalize text
        job_text = job_text.lower()
        job_text = re.sub(r'[^\w\s.-]', ' ', job_text)
        
        # Find all potential keywords
        words = re.findall(r'\b[\w.-]+\b', job_text)
        
        # Count tech keywords found
        keyword_counts = {}
        for keyword in self.tech_keywords:
            # Handle multi-word keywords
            if ' ' in keyword:
                count = len(re.findall(rf'\b{re.escape(keyword)}\b', job_text))
            else:
                count = words.count(keyword)
            
            if count > 0:
                keyword_counts[keyword] = count
        
        return keyword_counts
    
    def reorder_technologies(self, tech_section: List[Dict], matched_keywords: Dict[str, int]) -> List[Dict]:
        """Reorder technologies section to prioritize matched keywords"""
        if not tech_section:
            return tech_section
        
        def keyword_score(tech_item):
            """Calculate relevance score for a technology item"""
            details = tech_item.get('details', [])
            if isinstance(details, str):
                details = [details]
            
            score = 0
            for detail in details:
                detail_lower = detail.lower()
                for keyword, count in matched_keywords.items():
                    if keyword in detail_lower:
                        score += count * 10  # Weight matched keywords heavily
            
            return score
        
        # Sort by relevance score (descending)
        return sorted(tech_section, key=keyword_score, reverse=True)
    
    def enhance_summary(self, summary: str, top_keywords: List[str]) -> str:
        """Enhance summary with top keywords if not already present"""
        summary_lower = summary.lower()
        
        # Add top 3 keywords that aren't already mentioned
        keywords_to_add = []
        for keyword in top_keywords[:3]:
            if keyword not in summary_lower:
                keywords_to_add.append(keyword)
        
        if keywords_to_add:
            # Add keywords naturally to the end
            keyword_phrase = ", ".join(keywords_to_add)
            if summary.endswith('.'):
                summary = summary[:-1] + f", including expertise in {keyword_phrase}."
            else:
                summary += f" Experienced with {keyword_phrase}."
        
        return summary
    
    def add_relevant_skills(self, tech_section: List[Dict], matched_keywords: Dict[str, int]) -> List[Dict]:
        """Add a new section with job-specific keywords"""
        if not matched_keywords:
            return tech_section
        
        # Get top keywords not already prominently featured
        top_keywords = sorted(matched_keywords.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Check if we should add a "Job-Relevant Technologies" section
        existing_keywords = set()
        for section in tech_section:
            details = section.get('details', [])
            if isinstance(details, str):
                details = [details]
            for detail in details:
                existing_keywords.add(detail.lower())
        
        new_keywords = [kw for kw, _ in top_keywords if kw not in existing_keywords]
        
        if new_keywords:
            job_relevant_section = {
                'label': 'Job-Relevant Technologies',
                'details': new_keywords[:6]  # Top 6 missing keywords
            }
            # Insert at the beginning
            return [job_relevant_section] + tech_section
        
        return tech_section
    
    def optimize_resume(self, resume_data: Dict, job_keywords: Dict[str, int]) -> Dict:
        """Optimize resume based on job keywords"""
        optimized = resume_data.copy()
        
        if not job_keywords:
            print("No relevant keywords found in job posting")
            return optimized
        
        # Filter keywords to only include safe ones
        safe_keywords = self.filter_safe_keywords(job_keywords)
        
        if not safe_keywords:
            print("No safe keywords found that match your validated skills")
            return optimized
        
        print(f"Found {len(safe_keywords)} safe, relevant keywords:")
        for kw, count in sorted(safe_keywords.items(), key=lambda x: x[1], reverse=True)[:10]:
            skill_level = self.get_skill_level(kw)
            print(f"  - {kw}: {count} mentions ({skill_level})")
        
        # Enhance summary (only with expert/proficient skills)
        if 'cv' in optimized and 'summary' in optimized['cv']:
            expert_keywords = {kw: count for kw, count in safe_keywords.items() 
                             if self.validate_keyword(kw, 'proficient')}
            top_kw_list = [kw for kw, _ in sorted(expert_keywords.items(), key=lambda x: x[1], reverse=True)]
            optimized['cv']['summary'] = self.enhance_summary(
                optimized['cv']['summary'], 
                top_kw_list
            )
        
        # Optimize technologies section
        if 'cv' in optimized and 'sections' in optimized['cv'] and 'technologies' in optimized['cv']['sections']:
            tech_section = optimized['cv']['sections']['technologies']
            
            # Reorder existing technologies
            tech_section = self.reorder_technologies(tech_section, safe_keywords)
            
            # Add job-relevant technologies section (only familiar+ skills)
            relevant_keywords = {kw: count for kw, count in safe_keywords.items() 
                               if self.validate_keyword(kw, 'familiar')}
            tech_section = self.add_relevant_skills(tech_section, relevant_keywords)
            
            optimized['cv']['sections']['technologies'] = tech_section
        
        return optimized
    
    def get_skill_level(self, keyword: str) -> str:
        """Get the skill level for a keyword"""
        keyword_lower = keyword.lower()
        for level in ['expert', 'proficient', 'familiar', 'learning']:
            if keyword_lower in [skill.lower() for skill in self.validated_skills.get(level, [])]:
                return level
        return 'unknown'
    
    def save_resume(self, resume_data: Dict, output_path: str):
        """Save optimized resume to YAML file"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(resume_data, file, default_flow_style=False, 
                             allow_unicode=True, sort_keys=False)
            print(f"Optimized resume saved to: {output_path}")
        except Exception as e:
            print(f"Error saving resume: {e}")

def main():
    parser = argparse.ArgumentParser(description='Optimize resume for job posting keywords')
    parser.add_argument('resume_path', help='Path to base resume YAML file')
    parser.add_argument('job_path', help='Path to job posting text file')
    parser.add_argument('--output', '-o', help='Output path (optional)')
    parser.add_argument('--skills-config', '-s', help='Path to skills validation config', 
                       default='config/skills.yaml')
    
    args = parser.parse_args()
    
    optimizer = ResumeOptimizer(args.skills_config)
    
    # Load resume and job posting
    resume_data = optimizer.load_resume(args.resume_path)
    if not resume_data:
        return
    
    job_text = optimizer.load_job_posting(args.job_path)
    if not job_text:
        return
    
    # Extract keywords and optimize
    job_keywords = optimizer.extract_keywords(job_text)
    optimized_resume = optimizer.optimize_resume(resume_data, job_keywords)
    
    # Generate output filename
    if args.output:
        output_path = args.output
    else:
        job_name = Path(args.job_path).stem
        output_path = f"resumes/generated/optimized_resume_{job_name}.yaml"
    
    # Save optimized resume
    optimizer.save_resume(optimized_resume, output_path)

if __name__ == "__main__":
    main()