"""Debug script to test raw API calls."""

import requests


def test_nifc_api():
    """Test NIFC API directly."""
    print("=" * 80)
    print("Testing NIFC API")
    print("=" * 80)
    
    url = (
        "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
        "WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
    )
    
    # Try getting just 5 records
    params = {
        "where": "1=1",  # Get all records
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": 5,
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                print(f"Found {len(data['features'])} features")
                
                if data["features"]:
                    print("\nSample feature:")
                    sample = data["features"][0]
                    if "attributes" in sample:
                        attrs = sample["attributes"]
                        print(f"  Available fields: {list(attrs.keys())}")
                        print(f"  Incident Name: {attrs.get('IncidentName', 'N/A')}")
                        print(f"  Fire Discovery: {attrs.get('FireDiscoveryDateTime', 'N/A')}")
                        print(f"  Acres: {attrs.get('GISAcres', 'N/A')}")
            else:
                print("No 'features' in response")
                print(f"Response keys: {data.keys()}")
        else:
            print(f"Error: {response.text[:500]}")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()


def test_mtbs_api():
    """Test MTBS API directly."""
    print("=" * 80)
    print("Testing MTBS API")
    print("=" * 80)
    
    url = (
        "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/0/query"
    )
    
    # Try getting fires from 2020
    params = {
        "where": "Fire_Year=2020",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": 5,
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                print(f"Found {len(data['features'])} features")
                
                if data["features"]:
                    print("\nSample feature:")
                    sample = data["features"][0]
                    if "attributes" in sample:
                        attrs = sample["attributes"]
                        print(f"  Fire Name: {attrs.get('Fire_Name', 'N/A')}")
                        print(f"  Fire Year: {attrs.get('Fire_Year', 'N/A')}")
                        print(f"  Acres: {attrs.get('Acres', 'N/A')}")
            else:
                print("No 'features' in response")
                print(f"Response keys: {data.keys()}")
        else:
            print(f"Error: {response.text[:500]}")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()


if __name__ == "__main__":
    test_nifc_api()
    test_mtbs_api()
