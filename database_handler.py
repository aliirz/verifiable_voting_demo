from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import datetime

class Database:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the Database class with Supabase client.
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def store_vote_data(
        self,
        cnic: str,
        ballot_id: int,
        election_id: int,
        encryption: str,
        hash_value: str,
        random_factor: str,
        timestamp: datetime.datetime
    ) -> Dict[str, Any]:
        """
        Store vote data in the votes table.
        """
        if not timestamp.tzinfo:
            raise ValueError("vote_time must include timezone information.")

        data = {
            "cnic": cnic,
            "ballot_id": ballot_id,
            "election_id": election_id,
            "encrypted_vote": encryption,
            "vote_hash": hash_value,
            "randomness": random_factor,
            "time": timestamp.isoformat(),
        }
        response = self.supabase.table("votes").insert(data).execute()
        return response

    def retrieve_vote_data(self, cnic: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve vote data from the votes table by CNIC.
        """
        response = self.supabase.table("votes").select("*").eq("CNIC", cnic).execute()
        return response.data[0] if response.data else None

    def store_election_data(
        self,
        election_id: int,
        num_candidates: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        status: bool,
        results_visibility: bool,
        encrypted_sum: str,
        encrypted_randomness: str,
        decrypted_tally: str
    ) -> Dict[str, Any]:
        """
        Store election data in the elections table.
        """
        data = {
            "id": election_id,
            "num_candidates": num_candidates,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "ongoing": status,
            "results_visibility": results_visibility,
            "encrypted_sum": encrypted_sum,
            "combined_randomness": encrypted_randomness,
            "decrypted_tally": decrypted_tally,
        }
        response = self.supabase.table("elections").insert(data).execute()
        return response

    def store_candidate_data(self, election_id: int, candidates: List[dict]) -> Dict[str, Any]:
        """
        Store candidate data in the candidates table.
        """
        # Add election_id to each candidate's data
        data = [{"election_id": election_id, "name": candidate["name"], "cand_id": candidate["id"], "symbol": candidate["symbol"]} for candidate in candidates]
        
        # Insert the data into the 'candidates' table via supabase
        response = self.supabase.table("candidates").insert(data).execute()
        
        # Return the response from the insertion operation
        return response
    
    def get_votes_by_election(self, election_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all votes for a given election ID.
        """
        response = self.supabase.table("votes").select("*").eq("election_id", election_id).execute()
        return response.data if response.data else []

    def update_result_visibility(self, election_id: int, status: bool) -> Optional[Dict[str, Any]]:
        election_data = self.retrieve_election_data(election_id)

        if not election_data:
            return {"status": "error", "message": f"Election ID {election_id} not found"}

        # Check if the election status is False aka not ongoing currently
        if not election_data['ongoing']:
            # Update the results_visibility to True
            response = self.supabase.table("elections").update({"results_visibility": True}).eq("id", election_id).execute()
            
            if response.status_code == 200:
                return {"status": "success", "message": f"Results visibility updated for election ID {election_id}"}
            else:
                return {"status": "error", "message": f"Failed to update results visibility for election ID {election_id}"}
        
        return {"status": "skipped", "message": f"Election ID {election_id} is already ongoing; no update made"}

    def retrieve_last_election(self):
        response = self.supabase.table('elections').select('*').order('created_at', desc=True).limit(1).execute()

        if not response.data:
            return {"status": "error", "message": "No elections found"}
        return response.data[0]

    def end_election(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve most recent election and change status to False
        """
        # Retrieve the last election by ID
        response = self.supabase.table("elections").select("*").order("id", desc=True).limit(1).execute()
        if not response.data:
            return {"status": "error", "message": "No elections found"}

        last_election = response.data[0]  # Get the most recent election
        election_id = last_election["id"]

        # Update the status of the last election to True (ongoing)
        update_response = self.supabase.table("elections").update({"ongoing": False}).eq("id", election_id).execute()
        return update_response

    def retrieve_election_data(self, election_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve election data from the elections table by election ID.
        """
        response = self.supabase.table("elections").select("*").eq("election_id", election_id).execute()
        return response.data[0] if response.data else None
    
    def get_visible_election(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the first election with visible results (results_visibility=True).
        """
        response = self.supabase.table("elections").select("*").eq("results_visibility", True).limit(1).execute()
        if response.data:
            return response.data[0]  # Return the first visible election
        return None

    def check_admin_username(self, username: str) -> bool:
        """
        Check if an admin username exists in the admins table.
        """
        response = self.supabase.table("admins").select("username").eq("username", username).execute()
        print("Check username response: ", response)
        return bool(response.data)

    def check_admin_password(self, username: str, password: str) -> bool:
        """
        Check if the password matches the admin username in the admins table.
        """
        response = self.supabase.table("admins").select("password").eq("username", username).execute()
        if not response.data:
            return False
        print("Check pw response: ", response)
        return response.data[0]["password"] == password
