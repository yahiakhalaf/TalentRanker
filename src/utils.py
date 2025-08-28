from typing import  List, Optional
from pydantic import BaseModel, Field

class Contact(BaseModel):
    """Contact information model."""
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    website: Optional[str] = Field(None, description="Personal website or portfolio URL")
    location: Optional[str] = Field(None, description="Location (city, state/country)")


class Education(BaseModel):
    """Education information model."""
    degree: str = Field(description="Degree name (e.g., Bachelor of Science)")
    field_of_study: Optional[str] = Field(description="Major or field of study")
    institution: Optional[str] = Field(description="University or college name")
    graduation_year: Optional[str] = Field(None, description="Graduation year")
    gpa: Optional[float] = Field(None, description="GPA if mentioned")


class Certification(BaseModel):
    """Certification information model."""
    name: str = Field(description="Certification name")
    issuing_organization: str = Field(description="Organization that issued the certification")
    issue_date: Optional[str] = Field(None, description="Date when certification was obtained")
    expiration_date: Optional[str] = Field(None, description="Expiration date if applicable")


class Experience(BaseModel):
    """Work experience information model."""
    job_title: str = Field(description="Job title or position")
    company: str = Field(description="Company name")
    start_date: str = Field(description="Start date")
    end_date: Optional[str] = Field(None, description="End date (null if current position)")
    duration: Optional[str] = Field(None, description="Duration of employment")
    description: str = Field(description="Job responsibilities and achievements")
    technologies_used: List[str] = Field(default_factory=list, description="Technologies and tools used")


class Project(BaseModel):
    """Project information model."""
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies_used: List[str] = Field(default_factory=list, description="Technologies and tools used")
    duration: Optional[str] = Field(None, description="Project duration")


class DomainKnowledge(BaseModel):
    """Domain knowledge information model."""
    industries: List[str] = Field(default_factory=list, description="Industry experience (e.g., fintech, healthcare)")
    business_domains: List[str] = Field(default_factory=list, description="Business domain expertise")


class Award(BaseModel):
    """Award information model."""
    name: str = Field(description="Award name")
    issuing_organization: str = Field(description="Organization that gave the award")
    received_date: Optional[str] = Field(None, description="Date received")
    description: Optional[str] = Field(None, description="Award description")


class Publication(BaseModel):
    """Publication information model."""
    title: str = Field(description="Publication title")
    publication_venue: str = Field(description="Journal, conference, or platform")
    publication_date: Optional[str] = Field(None, description="Publication date")
    description: Optional[str] = Field(None, description="Brief description")


class Book(BaseModel):
    """Book information model."""
    title: str = Field(description="Book title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    publication_date: Optional[str] = Field(None, description="Publication date")
    description: Optional[str] = Field(None, description="Brief description")


class ResumeData(BaseModel):
    """Complete resume data model."""
    name: str = Field(description="Full name of the person")
    job_title: Optional[str] = Field(None, description="Current job title or desired position")
    summary: str = Field(description="Professional summary or objective")
    contact: Contact = Field(description="Contact information")
    languages: List[str] = Field(default_factory=list, description="Spoken languages")
    skills: List[str] = Field(default_factory=list, description="Technical and professional skills")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    certifications: List[Certification] = Field(default_factory=list, description="Professional certifications")
    experience: List[Experience] = Field(default_factory=list, description="Work experience")
    experience_duration: str = Field(description="Total years and months of experience without counting the overlapping between them (e.g., '2 years 3 months', '1.5 years')")
    projects: List[Project] = Field(default_factory=list, description="Notable projects")
    soft_skills: List[str] = Field(description="List of leadership skills and soft skills (e.g., organizing events, leading teams, teamwork).")
    domain_knowledge: DomainKnowledge = Field(description="Domain-specific knowledge and expertise")
    awards: List[Award] = Field(default_factory=list, description="Awards and recognitions")
    publications: List[Publication] = Field(default_factory=list, description="Publications and articles")
    books: List[Book] = Field(default_factory=list, description="Books authored or co-authored")


default_resume = ResumeData(
            name="Unknown",
            job_title=None,
            summary="",
            contact=Contact(),
            languages=[],
            skills=[],
            education=[],
            certifications=[],
            experience=[],
            experience_duration="",
            projects=[],
            soft_skills=[],
            domain_knowledge=DomainKnowledge(),
            awards=[],
            publications=[],
            books=[]
        )
