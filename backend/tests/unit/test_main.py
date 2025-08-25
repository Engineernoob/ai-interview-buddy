import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import io

from main import app


class TestMainRoutes:
    """Test main API routes."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "AI Interview Buddy API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
        assert data["endpoints"]["websocket"] == "/ws/audio"
        assert data["endpoints"]["upload"] == "/api/upload"

    def test_health_check_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "local_llm" in data["services"]
        assert "whisper" in data["services"]

    def test_config_endpoint(self, client):
        """Test the configuration endpoint."""
        response = client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "whisper_model" in data
        assert "llm_model" in data
        assert "use_local_llm" in data
        assert "features" in data
        
        expected_features = [
            "real_time_transcription",
            "local_llm_coaching",
            "resume_upload",
            "job_description_analysis",
            "intent_detection"
        ]
        
        for feature in expected_features:
            assert feature in data["features"]


class TestDocumentUpload:
    """Test document upload functionality."""
    
    @patch('main.extract_pdf_text')
    @patch('main.validate_pdf_content')
    @patch('main.retriever')
    def test_successful_document_upload(self, mock_retriever, mock_validate, mock_extract, client, sample_pdf_bytes, sample_job_description):
        """Test successful document upload."""
        # Mock successful validation and extraction
        mock_validate.return_value = (True, "Valid PDF")
        mock_extract.return_value = "Extracted resume text with sufficient content for testing purposes"
        mock_retriever.store_resume.return_value = True
        mock_retriever.store_job_description.return_value = True
        
        # Prepare file upload
        files = {
            'resume': ('resume.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        data = {
            'job_description': sample_job_description
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Documents uploaded successfully"
        
        # Verify mocks were called
        mock_validate.assert_called_once()
        mock_extract.assert_called_once()
        mock_retriever.store_resume.assert_called_once()
        mock_retriever.store_job_description.assert_called_once_with(sample_job_description)

    def test_upload_non_pdf_file(self, client):
        """Test uploading non-PDF file returns error."""
        files = {
            'resume': ('resume.txt', io.BytesIO(b'This is not a PDF'), 'text/plain')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        
        result = response.json()
        assert "Only PDF files are supported" in result["message"]

    def test_upload_oversized_file(self, client):
        """Test uploading oversized file returns error."""
        # Create a file larger than 10MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        
        files = {
            'resume': ('large_resume.pdf', io.BytesIO(large_content), 'application/pdf')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 413
        
        result = response.json()
        assert "File too large" in result["message"]

    @patch('main.validate_pdf_content')
    def test_upload_invalid_pdf(self, mock_validate, client, sample_pdf_bytes):
        """Test uploading invalid PDF returns error."""
        mock_validate.return_value = (False, "Not a valid PDF")
        
        files = {
            'resume': ('invalid.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        
        result = response.json()
        assert "Invalid PDF" in result["message"]

    @patch('main.extract_pdf_text')
    @patch('main.validate_pdf_content')
    def test_upload_pdf_insufficient_text(self, mock_validate, mock_extract, client, sample_pdf_bytes):
        """Test uploading PDF with insufficient text returns error."""
        mock_validate.return_value = (True, "Valid PDF")
        mock_extract.return_value = "Too short"  # Less than 50 characters
        
        files = {
            'resume': ('resume.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 422
        
        result = response.json()
        assert "Could not extract sufficient text" in result["message"]

    @patch('main.extract_pdf_text')
    @patch('main.validate_pdf_content')
    @patch('main.retriever')
    def test_upload_storage_failure(self, mock_retriever, mock_validate, mock_extract, client, sample_pdf_bytes):
        """Test upload when storage fails."""
        mock_validate.return_value = (True, "Valid PDF")
        mock_extract.return_value = "Extracted resume text with sufficient content for testing purposes"
        mock_retriever.store_resume.return_value = False  # Simulate storage failure
        
        files = {
            'resume': ('resume.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 500
        
        result = response.json()
        assert "Failed to store documents" in result["message"]

    def test_upload_missing_resume(self, client):
        """Test upload without resume file."""
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", data=data)
        assert response.status_code == 422  # FastAPI validation error

    def test_upload_missing_job_description(self, client, sample_pdf_bytes):
        """Test upload without job description."""
        files = {
            'resume': ('resume.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        
        response = client.post("/api/upload", files=files)
        assert response.status_code == 422  # FastAPI validation error


class TestErrorHandling:
    """Test error handling."""
    
    @patch('main.extract_pdf_text')
    def test_global_exception_handler(self, mock_extract, client, sample_pdf_bytes):
        """Test global exception handler catches and formats errors."""
        mock_extract.side_effect = Exception("Unexpected error occurred")
        
        files = {
            'resume': ('resume.pdf', io.BytesIO(sample_pdf_bytes), 'application/pdf')
        }
        data = {
            'job_description': 'Test job description'
        }
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 500
        
        result = response.json()
        assert "Upload failed" in result["message"]