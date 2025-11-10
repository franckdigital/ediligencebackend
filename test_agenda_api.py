"""
Script de test pour l'API Agenda
Teste tous les endpoints et fonctionnalités
"""
import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Remplacer par votre username
PASSWORD = "admin"  # Remplacer par votre password

class AgendaAPITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_rdv_id = None
        self.test_reunion_id = None
        
    def print_section(self, title):
        """Afficher un titre de section"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_result(self, test_name, success, message=""):
        """Afficher le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"      → {message}")
    
    def authenticate(self):
        """S'authentifier et obtenir un token JWT"""
        self.print_section("AUTHENTIFICATION")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/token/",
                json={"username": USERNAME, "password": PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.print_result("Authentification", True, f"Token obtenu")
                return True
            else:
                self.print_result("Authentification", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("Authentification", False, str(e))
            return False
    
    def test_get_rendezvous(self):
        """Tester GET /api/rendezvous/"""
        self.print_section("TEST GET RENDEZ-VOUS")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/rendezvous/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_result("GET /api/rendezvous/", True, f"{count} rendez-vous trouvés")
                return True
            else:
                self.print_result("GET /api/rendezvous/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("GET /api/rendezvous/", False, str(e))
            return False
    
    def test_create_rendezvous(self):
        """Tester POST /api/rendezvous/"""
        self.print_section("TEST CREATE RENDEZ-VOUS")
        
        # Obtenir la liste des utilisateurs
        try:
            users_response = requests.get(
                f"{BASE_URL}/api/users/",
                headers=self.headers
            )
            users = users_response.json()
            
            if len(users) < 2:
                self.print_result("Créer rendez-vous", False, "Pas assez d'utilisateurs")
                return False
            
            participant_id = users[1]['id'] if len(users) > 1 else users[0]['id']
            
        except Exception as e:
            self.print_result("Récupérer utilisateurs", False, str(e))
            return False
        
        # Créer le rendez-vous
        now = datetime.now()
        data = {
            "titre": "Test API - Rendez-vous",
            "description": "Rendez-vous créé par le script de test",
            "date_debut": (now + timedelta(days=1)).isoformat(),
            "date_fin": (now + timedelta(days=1, hours=1)).isoformat(),
            "lieu": "Bureau de test",
            "participant": participant_id,
            "mode": "presentiel",
            "commentaires": "Test automatique"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/rendezvous/",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.test_rdv_id = result.get('id')
                self.print_result("POST /api/rendezvous/", True, f"ID: {self.test_rdv_id}")
                return True
            else:
                self.print_result("POST /api/rendezvous/", False, f"Status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_result("POST /api/rendezvous/", False, str(e))
            return False
    
    def test_update_rendezvous(self):
        """Tester PATCH /api/rendezvous/{id}/"""
        self.print_section("TEST UPDATE RENDEZ-VOUS")
        
        if not self.test_rdv_id:
            self.print_result("Update rendez-vous", False, "Pas de rendez-vous de test")
            return False
        
        data = {
            "titre": "Test API - Rendez-vous (Modifié)",
            "description": "Description mise à jour"
        }
        
        try:
            response = requests.patch(
                f"{BASE_URL}/api/rendezvous/{self.test_rdv_id}/",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                self.print_result("PATCH /api/rendezvous/{id}/", True, "Rendez-vous modifié")
                return True
            else:
                self.print_result("PATCH /api/rendezvous/{id}/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("PATCH /api/rendezvous/{id}/", False, str(e))
            return False
    
    def test_change_statut_rendezvous(self):
        """Tester POST /api/rendezvous/{id}/changer_statut/"""
        self.print_section("TEST CHANGER STATUT RENDEZ-VOUS")
        
        if not self.test_rdv_id:
            self.print_result("Changer statut", False, "Pas de rendez-vous de test")
            return False
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/rendezvous/{self.test_rdv_id}/changer_statut/",
                headers=self.headers,
                json={"statut": "en_cours"}
            )
            
            if response.status_code == 200:
                self.print_result("POST /api/rendezvous/{id}/changer_statut/", True, "Statut changé en 'en_cours'")
                return True
            else:
                self.print_result("POST /api/rendezvous/{id}/changer_statut/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("POST /api/rendezvous/{id}/changer_statut/", False, str(e))
            return False
    
    def test_get_reunions(self):
        """Tester GET /api/reunions/"""
        self.print_section("TEST GET RÉUNIONS")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/reunions/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_result("GET /api/reunions/", True, f"{count} réunions trouvées")
                return True
            else:
                self.print_result("GET /api/reunions/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("GET /api/reunions/", False, str(e))
            return False
    
    def test_create_reunion(self):
        """Tester POST /api/reunions/"""
        self.print_section("TEST CREATE RÉUNION")
        
        # Obtenir la liste des utilisateurs
        try:
            users_response = requests.get(
                f"{BASE_URL}/api/users/",
                headers=self.headers
            )
            users = users_response.json()
            
            if len(users) < 2:
                self.print_result("Créer réunion", False, "Pas assez d'utilisateurs")
                return False
            
            participant_ids = [u['id'] for u in users[:3]]  # Prendre les 3 premiers
            
        except Exception as e:
            self.print_result("Récupérer utilisateurs", False, str(e))
            return False
        
        # Créer la réunion
        now = datetime.now()
        data = {
            "intitule": "Test API - Réunion",
            "description": "Réunion créée par le script de test",
            "type_reunion": "en_ligne",
            "date_debut": (now + timedelta(days=2)).isoformat(),
            "date_fin": (now + timedelta(days=2, hours=2)).isoformat(),
            "lieu": "Zoom",
            "lien_zoom": "https://zoom.us/j/test123",
            "participants": participant_ids,
            "compte_rendu": "Test automatique"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/reunions/",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.test_reunion_id = result.get('id')
                self.print_result("POST /api/reunions/", True, f"ID: {self.test_reunion_id}")
                return True
            else:
                self.print_result("POST /api/reunions/", False, f"Status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_result("POST /api/reunions/", False, str(e))
            return False
    
    def test_mes_rendezvous(self):
        """Tester GET /api/rendezvous/mes_rendezvous/"""
        self.print_section("TEST MES RENDEZ-VOUS")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/rendezvous/mes_rendezvous/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data)
                self.print_result("GET /api/rendezvous/mes_rendezvous/", True, f"{count} rendez-vous")
                return True
            else:
                self.print_result("GET /api/rendezvous/mes_rendezvous/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("GET /api/rendezvous/mes_rendezvous/", False, str(e))
            return False
    
    def test_mes_reunions(self):
        """Tester GET /api/reunions/mes_reunions/"""
        self.print_section("TEST MES RÉUNIONS")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/reunions/mes_reunions/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data)
                self.print_result("GET /api/reunions/mes_reunions/", True, f"{count} réunions")
                return True
            else:
                self.print_result("GET /api/reunions/mes_reunions/", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("GET /api/reunions/mes_reunions/", False, str(e))
            return False
    
    def cleanup(self):
        """Nettoyer les données de test"""
        self.print_section("NETTOYAGE")
        
        # Supprimer le rendez-vous de test
        if self.test_rdv_id:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/rendezvous/{self.test_rdv_id}/",
                    headers=self.headers
                )
                if response.status_code in [200, 204]:
                    self.print_result("Supprimer rendez-vous de test", True)
                else:
                    self.print_result("Supprimer rendez-vous de test", False, f"Status: {response.status_code}")
            except Exception as e:
                self.print_result("Supprimer rendez-vous de test", False, str(e))
        
        # Supprimer la réunion de test
        if self.test_reunion_id:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/reunions/{self.test_reunion_id}/",
                    headers=self.headers
                )
                if response.status_code in [200, 204]:
                    self.print_result("Supprimer réunion de test", True)
                else:
                    self.print_result("Supprimer réunion de test", False, f"Status: {response.status_code}")
            except Exception as e:
                self.print_result("Supprimer réunion de test", False, str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "TEST API MODULE AGENDA" + " " * 31 + "║")
        print("╚" + "═" * 68 + "╝")
        
        tests = [
            ("Authentification", self.authenticate),
            ("GET Rendez-vous", self.test_get_rendezvous),
            ("CREATE Rendez-vous", self.test_create_rendezvous),
            ("UPDATE Rendez-vous", self.test_update_rendezvous),
            ("CHANGE STATUT Rendez-vous", self.test_change_statut_rendezvous),
            ("GET Réunions", self.test_get_reunions),
            ("CREATE Réunion", self.test_create_reunion),
            ("MES Rendez-vous", self.test_mes_rendezvous),
            ("MES Réunions", self.test_mes_reunions),
        ]
        
        results = []
        for test_name, test_func in tests:
            result = test_func()
            results.append((test_name, result))
        
        # Nettoyage
        self.cleanup()
        
        # Résumé
        self.print_section("RÉSUMÉ DES TESTS")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\n  Tests réussis : {passed}/{total}")
        print(f"  Taux de réussite : {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n  🎉 TOUS LES TESTS SONT PASSÉS !")
        else:
            print("\n  ⚠️  Certains tests ont échoué. Vérifiez les logs ci-dessus.")
        
        print("\n" + "=" * 70 + "\n")

if __name__ == '__main__':
    tester = AgendaAPITester()
    tester.run_all_tests()
