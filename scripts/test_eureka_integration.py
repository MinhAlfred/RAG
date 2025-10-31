"""Test Eureka Service Discovery Integration"""

import os
import time
import requests
import json
from typing import Dict, Any


def check_eureka_server(eureka_url: str = "http://localhost:8761") -> bool:
    """Check if Eureka server is running"""
    try:
        response = requests.get(f"{eureka_url}/actuator/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Eureka server is running at {eureka_url}")
            return True
        else:
            print(f"⚠️ Eureka server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Eureka server at {eureka_url}")
        return False
    except Exception as e:
        print(f"❌ Error checking Eureka: {e}")
        return False


def check_service_registration(
    eureka_url: str = "http://localhost:8761",
    app_name: str = "PYTHON-RAG-SERVICE"
) -> bool:
    """Check if Python service is registered in Eureka"""
    try:
        # Get all registered apps
        response = requests.get(
            f"{eureka_url}/eureka/apps",
            headers={"Accept": "application/json"},
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch apps from Eureka: {response.status_code}")
            return False
        
        data = response.json()
        applications = data.get("applications", {}).get("application", [])
        
        # Find our service
        for app in applications:
            if isinstance(app, dict) and app.get("name") == app_name:
                instances = app.get("instance", [])
                if not isinstance(instances, list):
                    instances = [instances]
                
                print(f"\n✅ Found {app_name} in Eureka registry:")
                print(f"   Total instances: {len(instances)}")
                
                for i, instance in enumerate(instances, 1):
                    print(f"\n   Instance {i}:")
                    print(f"      Status: {instance.get('status')}")
                    print(f"      Host: {instance.get('hostName')}:{instance.get('port', {}).get('$', 'N/A')}")
                    print(f"      IP: {instance.get('ipAddr')}")
                    print(f"      Health Check: {instance.get('healthCheckUrl')}")
                    
                    metadata = instance.get('metadata', {})
                    if metadata:
                        print(f"      Metadata:")
                        for key, value in metadata.items():
                            print(f"         {key}: {value}")
                
                return True
        
        print(f"❌ {app_name} not found in Eureka registry")
        print(f"   Registered apps: {[app.get('name') for app in applications if isinstance(app, dict)]}")
        return False
        
    except Exception as e:
        print(f"❌ Error checking registration: {e}")
        return False


def test_python_service(port: int = 8000) -> bool:
    """Test if Python RAG service is accessible"""
    try:
        # Test health endpoint
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"\n✅ Python RAG service is healthy:")
            print(f"   Status: {health_data.get('status')}")
            print(f"   RAG Status: {health_data.get('rag_status')}")
            print(f"   Version: {health_data.get('version')}")
            return True
        else:
            print(f"⚠️ Python service returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Python service at localhost:{port}")
        return False
    except Exception as e:
        print(f"❌ Error testing Python service: {e}")
        return False


def test_service_call_via_name() -> bool:
    """
    Test calling Python service via Eureka service name
    Note: This requires Spring Boot with Feign Client to work
    """
    print("\n📝 Note: Service name resolution requires Spring Boot + Feign Client + Eureka")
    print("   For testing from Python, we use direct URL")
    print("\n   Spring Boot với Feign Client:")
    print("   ```java")
    print("   @FeignClient(name = \"python-rag-service\")")
    print("   public interface PythonRagClient {")
    print("       @GetMapping(\"/health\")")
    print("       HealthResponse health();")
    print("   }")
    print("   ```")
    
    try:
        # In Spring Boot with Feign: pythonRagClient.health()
        # Here we test with direct URL
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("\n✅ Service is callable (tested with direct URL)")
            print("   In Spring Boot Feign: pythonRagClient.health()")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_slide_generation() -> bool:
    """Test slide generation endpoint"""
    try:
        url = "http://localhost:8000/slides/generate/json"
        request_data = {
            "topic": "Test Eureka Integration",
            "grade": 10,
            "slide_count": 3,
            "include_examples": False,
            "include_exercises": False
        }
        
        print(f"\n🧪 Testing slide generation...")
        response = requests.post(url, json=request_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Slide generation successful:")
            print(f"   Title: {data.get('title')}")
            print(f"   Slides: {len(data.get('slides', []))}")
            print(f"   Status: {data.get('status')}")
            print(f"   Processing time: {data.get('processing_time')}s")
            return True
        else:
            print(f"❌ Slide generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing slide generation: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 Testing Eureka Service Discovery Integration")
    print("=" * 70)
    
    # Test 1: Check Eureka server
    print("\n[1/5] Checking Eureka Server...")
    eureka_ok = check_eureka_server()
    
    if not eureka_ok:
        print("\n⚠️ Eureka server is not running!")
        print("   Start Eureka server first:")
        print("   - Spring Boot Eureka: mvn spring-boot:run")
        print("   - Docker: docker-compose up eureka-server")
        return
    
    # Test 2: Check Python service
    print("\n[2/5] Checking Python RAG Service...")
    python_ok = test_python_service()
    
    if not python_ok:
        print("\n⚠️ Python RAG service is not running!")
        print("   Start Python service:")
        print("   - python scripts/run_api.py")
        return
    
    # Test 3: Check registration
    print("\n[3/5] Checking Service Registration...")
    time.sleep(2)  # Wait for registration
    registered = check_service_registration()
    
    if not registered:
        print("\n⚠️ Service not registered in Eureka!")
        print("   Possible causes:")
        print("   - EUREKA_SERVER environment variable not set")
        print("   - Network connectivity issues")
        print("   - Eureka registration failed (check Python logs)")
        return
    
    # Test 4: Test service call
    print("\n[4/5] Testing Service Call...")
    call_ok = test_service_call_via_name()
    
    # Test 5: Test slide generation
    print("\n[5/5] Testing Slide Generation...")
    slide_ok = test_slide_generation()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"   Eureka Server:        {'✅ OK' if eureka_ok else '❌ Failed'}")
    print(f"   Python Service:       {'✅ OK' if python_ok else '❌ Failed'}")
    print(f"   Service Registration: {'✅ OK' if registered else '❌ Failed'}")
    print(f"   Service Call:         {'✅ OK' if call_ok else '❌ Failed'}")
    print(f"   Slide Generation:     {'✅ OK' if slide_ok else '❌ Failed'}")
    
    if all([eureka_ok, python_ok, registered, call_ok, slide_ok]):
        print("\n✅ All tests passed! Eureka integration is working correctly.")
        print("\n📚 Next steps - Spring Boot với Feign Client:")
        print("   1. Add dependencies:")
        print("      - spring-cloud-starter-netflix-eureka-client")
        print("      - spring-cloud-starter-openfeign")
        print("   2. Enable Feign: @EnableFeignClients")
        print("   3. Create Feign interface:")
        print("      @FeignClient(name = \"python-rag-service\")")
        print("      public interface PythonRagClient { ... }")
        print("   4. Inject và sử dụng:")
        print("      @Autowired PythonRagClient pythonRagClient;")
        print("\n   📖 Full guide: docs/EUREKA_FEIGN_INTEGRATION.md")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
