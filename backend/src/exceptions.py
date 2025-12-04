"""
Custom exceptions for Batfish visualization backend.

Provides structured exception handling for Batfish-related errors.
"""


class BatfishException(Exception):
    """
    Base exception for Batfish-related errors.

    Raised when Batfish operations fail, including:
    - Connection errors to Batfish service
    - Query execution failures
    - Snapshot initialization errors
    - Configuration parsing errors

    This exception is caught by the error handler middleware
    and converted to a structured JSON error response.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize Batfish exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class SnapshotException(BatfishException):
    """
    Exception for snapshot-related operations.

    Raised when snapshot operations fail, such as:
    - Snapshot creation with invalid configurations
    - Snapshot not found
    - Snapshot deletion errors
    """

    pass


class TopologyException(BatfishException):
    """
    Exception for topology query operations.

    Raised when topology extraction fails, such as:
    - Failed to retrieve nodes
    - Failed to retrieve edges
    - Failed to retrieve interface properties
    """

    pass


class VerificationException(BatfishException):
    """
    Exception for verification query operations.

    Raised when verification queries fail, such as:
    - Reachability query errors
    - ACL verification errors
    - Routing table query errors
    """

    pass


class FileUploadException(Exception):
    """
    Exception for file upload operations.

    Raised when file upload operations fail, such as:
    - Invalid file format
    - File size limit exceeded
    - File sanitization errors
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize file upload exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message
