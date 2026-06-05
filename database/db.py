import sqlite3
import json
import os
from typing import Dict, Any, List, Tuple, Optional

class DatabaseManager:
    """
    Manages SQLite database connections and executes CRUD queries for the ATS system.
    Follows OOP principles.
    """

    def __init__(self, db_path: str = "resume_screening.db"):
        """
        Initialize the database and verify schemas.
        """
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a standard sqlite3 Connection object."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable dictionary rows
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Creates the SQLite tables if they do not exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS Candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                file_path TEXT,
                raw_text TEXT,
                parsed_skills TEXT,       -- JSON string
                parsed_education TEXT,    -- TEXT or JSON
                parsed_experience TEXT,   -- TEXT or JSON
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES Candidates(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS JobDescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                required_skills TEXT,     -- JSON string
                min_experience REAL DEFAULT 0.0,
                education_requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS MatchResults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                jd_id INTEGER,
                match_percentage REAL,
                ats_score REAL,
                skills_found TEXT,        -- JSON string
                skills_missing TEXT,      -- JSON string
                feedback TEXT,            -- JSON string
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES Resumes(id) ON DELETE CASCADE,
                FOREIGN KEY (jd_id) REFERENCES JobDescriptions(id) ON DELETE CASCADE
            );
            """
        ]

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database Initialization Error: {e}")
            raise e
        finally:
            conn.close()

    # --- CRUD operations for Candidates ---
    
    def add_candidate(self, name: str, email: str = None, phone: str = None) -> int:
        """
        Inserts a new candidate. If candidate email already exists, returns the existing candidate's id.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # If email is provided, check if candidate already exists
            if email:
                cursor.execute("SELECT id FROM Candidates WHERE email = ?", (email,))
                row = cursor.fetchone()
                if row:
                    return row["id"]

            cursor.execute(
                "INSERT INTO Candidates (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add candidate: {e}")
        finally:
            conn.close()

    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a candidate by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Candidates WHERE id = ?", (candidate_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # --- CRUD operations for Resumes ---
    
    def add_resume(self, candidate_id: int, file_path: str, raw_text: str, 
                   parsed_skills: List[str] = None, parsed_education: str = "", 
                   parsed_experience: str = "") -> int:
        """
        Inserts a new resume. parsed_skills is passed as a list and stored as a JSON string.
        """
        conn = self._get_connection()
        skills_json = json.dumps(parsed_skills or [])
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Resumes (candidate_id, file_path, raw_text, parsed_skills, parsed_education, parsed_experience)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (candidate_id, file_path, raw_text, skills_json, parsed_education, parsed_experience)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add resume: {e}")
        finally:
            conn.close()

    def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a resume by ID and deserializes parsed_skills."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["parsed_skills"] = json.loads(res["parsed_skills"]) if res["parsed_skills"] else []
            return res
        finally:
            conn.close()

    # --- CRUD operations for JobDescriptions ---
    
    def add_job_description(self, title: str, raw_text: str, required_skills: List[str] = None, 
                            min_experience: float = 0.0, education_requirements: str = "") -> int:
        """
        Inserts a job description. required_skills is stored as a JSON string.
        """
        conn = self._get_connection()
        skills_json = json.dumps(required_skills or [])
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO JobDescriptions (title, raw_text, required_skills, min_experience, education_requirements)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, raw_text, skills_json, min_experience, education_requirements)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add job description: {e}")
        finally:
            conn.close()

    def get_job_description(self, jd_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a Job Description by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM JobDescriptions WHERE id = ?", (jd_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["required_skills"] = json.loads(res["required_skills"]) if res["required_skills"] else []
            return res
        finally:
            conn.close()

    def get_all_job_descriptions(self) -> List[Dict[str, Any]]:
        """Retrieves all stored job descriptions."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, min_experience, education_requirements, created_at FROM JobDescriptions ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # --- CRUD operations for MatchResults ---
    
    def add_match_result(self, resume_id: int, jd_id: int, match_percentage: float, 
                         ats_score: float, skills_found: List[str] = None, 
                         skills_missing: List[str] = None, feedback: Dict[str, Any] = None) -> int:
        """
        Inserts a comparison match result.
        """
        conn = self._get_connection()
        found_json = json.dumps(skills_found or [])
        missing_json = json.dumps(skills_missing or [])
        feedback_json = json.dumps(feedback or {})
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO MatchResults (resume_id, jd_id, match_percentage, ats_score, skills_found, skills_missing, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (resume_id, jd_id, match_percentage, ats_score, found_json, missing_json, feedback_json)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add match result: {e}")
        finally:
            conn.close()

    def get_leaderboard(self, jd_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves candidates matching a job description, ranked by match_percentage DESC.
        Joins Candidates, Resumes, and MatchResults.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    c.name as candidate_name,
                    c.email as candidate_email,
                    r.file_path,
                    m.id as result_id,
                    m.match_percentage,
                    m.ats_score,
                    m.skills_found,
                    m.skills_missing,
                    m.analyzed_at
                FROM MatchResults m
                JOIN Resumes r ON m.resume_id = r.id
                JOIN Candidates c ON r.candidate_id = c.id
                WHERE m.jd_id = ?
                ORDER BY m.match_percentage DESC, m.ats_score DESC
                """,
                (jd_id,)
            )
            rows = cursor.fetchall()
            leaderboard = []
            for row in rows:
                item = dict(row)
                item["skills_found"] = json.loads(item["skills_found"]) if item["skills_found"] else []
                item["skills_missing"] = json.loads(item["skills_missing"]) if item["skills_missing"] else []
                leaderboard.append(item)
            return leaderboard
        finally:
            conn.close()
            
    def delete_job_description(self, jd_id: int):
        """Deletes a job description and cascades to related MatchResults."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM JobDescriptions WHERE id = ?", (jd_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete job description: {e}")
        finally:
            conn.close()
