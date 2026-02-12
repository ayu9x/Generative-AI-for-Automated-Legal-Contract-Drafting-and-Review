"""Document Processing Utilities."""

import re
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class DocumentProcessor:
    """Utility for processing and analyzing legal documents."""

    # Legal clause type patterns
    CLAUSE_PATTERNS = {
        "definitions": r"(?:ARTICLE|Section)\s+\d+\.?\s*(?:DEFINITIONS?|INTERPRETATION)",
        "confidentiality": r"(?:ARTICLE|Section)\s+\d+\.?\s*CONFIDENTIAL",
        "indemnification": r"(?:ARTICLE|Section)\s+\d+\.?\s*INDEMNIF",
        "limitation_of_liability": r"(?:ARTICLE|Section)\s+\d+\.?\s*LIMITATION\s+OF\s+LIABILITY",
        "governing_law": r"(?:ARTICLE|Section)\s+\d+\.?\s*GOVERNING\s+LAW",
        "termination": r"(?:ARTICLE|Section)\s+\d+\.?\s*TERM(?:INATION)?",
        "force_majeure": r"(?:ARTICLE|Section)\s+\d+\.?\s*FORCE\s+MAJEURE",
        "intellectual_property": r"(?:ARTICLE|Section)\s+\d+\.?\s*INTELLECTUAL\s+PROPERTY",
        "data_protection": r"(?:ARTICLE|Section)\s+\d+\.?\s*DATA\s+PROTECT",
        "dispute_resolution": r"(?:ARTICLE|Section)\s+\d+\.?\s*DISPUTE\s+RESOLUTION",
        "representations": r"(?:ARTICLE|Section)\s+\d+\.?\s*REPRESENTATIONS?\s+AND\s+WARRANTIES",
        "payment": r"(?:ARTICLE|Section)\s+\d+\.?\s*(?:PAYMENT|COMPENSATION|FEES)",
        "scope": r"(?:ARTICLE|Section)\s+\d+\.?\s*SCOPE\s+OF\s+(?:SERVICES?|WORK)",
    }

    @staticmethod
    def extract_metadata(content: str) -> Dict[str, Any]:
        """Extract metadata from a legal document."""
        metadata = {
            "word_count": len(content.split()),
            "character_count": len(content),
            "line_count": len(content.splitlines()),
            "page_estimate": max(1, len(content.split()) // 250),  # ~250 words per page
        }

        # Extract dates
        date_pattern = r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b'
        dates = re.findall(date_pattern, content, re.IGNORECASE)
        metadata["dates_found"] = dates[:5]

        # Extract monetary values
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?)\b'
        values = re.findall(money_pattern, content, re.IGNORECASE)
        metadata["monetary_values"] = values[:10]

        # Extract party names (simplified)
        party_pattern = r'(?:between|by and between)\s+([^,\n]+?)(?:\s*,|\s+and\s+)'
        parties = re.findall(party_pattern, content, re.IGNORECASE)
        metadata["parties_detected"] = [p.strip() for p in parties[:5]]

        # Detect contract type
        metadata["detected_type"] = DocumentProcessor.detect_contract_type(content)

        # Detect language (simplified)
        metadata["language"] = "en"  # Default; would use langdetect in production

        return metadata

    @staticmethod
    def detect_contract_type(content: str) -> str:
        """Detect the type of contract from its content."""
        content_lower = content.lower()

        type_indicators = {
            "nda": ["non-disclosure", "confidentiality agreement", "nda", "mutual non-disclosure"],
            "msa": ["master service agreement", "master services agreement", "msa"],
            "employment": ["employment agreement", "employment contract", "employee", "employer"],
            "service_agreement": ["service agreement", "consulting agreement", "professional services"],
            "license": ["license agreement", "software license", "licensing", "licensor", "licensee"],
            "lease": ["lease agreement", "landlord", "tenant", "premises", "rental"],
            "partnership": ["partnership agreement", "general partner", "limited partner"],
            "merger_acquisition": ["merger", "acquisition", "purchase agreement", "asset purchase"],
            "loan": ["loan agreement", "promissory note", "borrower", "lender", "principal amount"],
            "supply": ["supply agreement", "supplier", "supply chain"],
            "distribution": ["distribution agreement", "distributor", "territory"],
            "franchise": ["franchise agreement", "franchisee", "franchisor"],
            "settlement": ["settlement agreement", "settlement", "release of claims"],
        }

        scores = {}
        for contract_type, keywords in type_indicators.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[contract_type] = score

        if scores:
            return max(scores, key=scores.get)
        return "custom"

    @staticmethod
    def extract_clauses(content: str) -> List[Dict[str, Any]]:
        """Extract individual clauses from contract content."""
        clauses = []
        lines = content.split('\n')

        current_clause = None
        current_lines = []
        clause_number = 0

        article_pattern = re.compile(
            r'^(?:ARTICLE|SECTION)\s+(\d+\.?\d*)\s*[.:]\s*(.*?)$|'
            r'^(\d+\.)\s+([A-Z][A-Z\s]+)$',
            re.IGNORECASE
        )

        for line in lines:
            match = article_pattern.match(line.strip())
            if match:
                # Save previous clause
                if current_clause:
                    current_clause["content"] = '\n'.join(current_lines).strip()
                    if current_clause["content"]:
                        clauses.append(current_clause)

                groups = match.groups()
                number = groups[0] or groups[2] or ""
                title = groups[1] or groups[3] or ""
                clause_number += 1

                # Detect clause type
                clause_type = "general"
                for ct, pattern in DocumentProcessor.CLAUSE_PATTERNS.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        clause_type = ct
                        break

                current_clause = {
                    "number": number.strip('.'),
                    "title": title.strip(),
                    "type": clause_type,
                    "position": clause_number,
                }
                current_lines = [line]
            elif current_clause:
                current_lines.append(line)

        # Add last clause
        if current_clause:
            current_clause["content"] = '\n'.join(current_lines).strip()
            if current_clause["content"]:
                clauses.append(current_clause)

        return clauses

    @staticmethod
    def search_in_document(
        content: str,
        query: str,
        context_chars: int = 200,
    ) -> List[Dict[str, Any]]:
        """Search for text within a document, returning matches with context."""
        results = []
        content_lower = content.lower()
        query_lower = query.lower()

        start = 0
        while True:
            idx = content_lower.find(query_lower, start)
            if idx == -1:
                break

            context_start = max(0, idx - context_chars)
            context_end = min(len(content), idx + len(query) + context_chars)
            context = content[context_start:context_end]

            # Count line number
            line_number = content[:idx].count('\n') + 1

            results.append({
                "position": idx,
                "line_number": line_number,
                "matched_text": content[idx:idx + len(query)],
                "context": context,
            })

            start = idx + 1

        return results

    @staticmethod
    def sanitize_content(content: str) -> str:
        """Sanitize document content for safe processing."""
        # Remove potentially dangerous content
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)

        # Normalize whitespace
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove null bytes
        content = content.replace('\x00', '')

        return content

    @staticmethod
    def format_for_export(
        content: str,
        format_type: str = "plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format contract content for export."""
        if format_type == "markdown":
            # Convert to markdown-friendly format
            content = re.sub(r'^(ARTICLE\s+\d+\.?\s*.+)$', r'## \1', content, flags=re.MULTILINE)
            content = re.sub(r'^(\d+\.\d+\s+.+)$', r'### \1', content, flags=re.MULTILINE)
            return content

        elif format_type == "html":
            html = "<html><body>"
            html += f"<h1>Contract Document</h1>"
            if metadata:
                html += f"<p><em>Generated: {metadata.get('created_at', 'N/A')}</em></p>"

            for line in content.split('\n'):
                if re.match(r'^ARTICLE\s+\d+', line, re.IGNORECASE):
                    html += f"<h2>{line}</h2>"
                elif re.match(r'^\d+\.\d+\s+', line):
                    html += f"<h3>{line}</h3>"
                elif line.strip():
                    html += f"<p>{line}</p>"

            html += "</body></html>"
            return html

        return content  # plain text


# Singleton instance
document_processor = DocumentProcessor()
