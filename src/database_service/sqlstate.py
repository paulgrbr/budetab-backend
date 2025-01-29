SQLSTATE_TO_HTTP_STATUS = {
    # Class 23 — Integrity Constraint Violation
    '23505': 409,  # Conflict: Unique violation
    '23503': 400,  # Bad Request: Foreign key violation
    '23502': 400,  # Bad Request: Not null violation
    '23514': 400,  # Bad Request: Check constraint violation
    '23P01': 400,  # Bad Request: Exclusion violation

    # Class 22 — Data Exception
    '22001': 400,  # Bad Request: String data, right truncation
    '22007': 400,  # Bad Request: Invalid datetime format
    '22008': 400,  # Bad Request: Datetime field overflow
    '22012': 400,  # Bad Request: Division by zero
    '22018': 400,  # Bad Request: Invalid character value for cast
    '22021': 400,  # Bad Request: Character not in repertoire
    '22022': 400,  # Bad Request: Indicator variable required but not supplied
    '22025': 400,  # Bad Request: Invalid escape sequence
    '22P02': 400,  # Bad Request: Invalid text representation
    '22P03': 400,  # Bad Request: Invalid binary representation
    '22P04': 400,  # Bad Request: Bad copy file format
    '22P05': 400,  # Bad Request: Untranslatable character

    # Class 08 — Connection Exception
    '08001': 503,  # Service Unavailable: SQL client unable to establish connection
    '08003': 503,  # Service Unavailable: Connection does not exist
    '08006': 503,  # Service Unavailable: Connection failure
    '08004': 403,  # Forbidden: SQL server rejected establishment of connection

    # Class 25 — Invalid Transaction State
    '25001': 409,  # Conflict: Active SQL transaction
    '25002': 409,  # Conflict: Branch transaction already active
    '25003': 409,  # Conflict: Inappropriate access mode for branch transaction
    '25004': 409,  # Conflict: Inappropriate isolation level for branch transaction

    # Class 42 — Syntax Error or Access Rule Violation
    '42601': 400,  # Bad Request: Syntax error
    '42501': 403,  # Forbidden: Insufficient privilege
    '42846': 400,  # Bad Request: Cannot coerce
    '42883': 400,  # Bad Request: Undefined function
    '42P01': 400,  # Bad Request: Undefined table
    '42P02': 400,  # Bad Request: Undefined parameter
    '42P07': 400,  # Bad Request: Duplicate table
    '42P10': 400,  # Bad Request: Invalid column reference

    # Class XX — Internal Errors
    'XX000': 500,  # Internal Server Error: Internal error
    'XX001': 500,  # Internal Server Error: Data corrupted
    'XX002': 500,  # Internal Server Error: Index corrupted
}

def map_sqlstate_to_http_status(code):
    # Maps a PostgreSQL SQLSTATE code to an HTTP status code.
    try:
        return int(SQLSTATE_TO_HTTP_STATUS.get(code))
    except:
        return 500