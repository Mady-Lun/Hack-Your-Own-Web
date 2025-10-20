from pydantic import BaseModel, Field, validator
import re


class ValidDomainSchema(BaseModel):
    domain: str = Field(..., description="The URL of the site to scan")

    @validator('domain')
    def validate_domain(cls, v):
        # Basic domain regex: allows subdomains, letters, numbers, hyphens, and TLDs
        pattern = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid domain format")
        return v