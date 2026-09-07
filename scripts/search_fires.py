"""Search for fires by year and location to find correct names."""

from datetime import date

from firetwin.data.clients import MTBSClient, NIFCClient


def search_2020_california_fires():
    """Search for 2020 California fires in NIFC and MTBS."""
    print("=" * 80)
    print("Searching for 2020 California Fires")
    print("=" * 80)
    print()
    
    # NIFC search
    print("NIFC Database Search")
    print("-" * 80)
    nifc = NIFCClient()
    
    try:
        # Get all current perimeters (this may include historical)
        print("Fetching NIFC perimeters...")
        perimeters = nifc.get_current_perimeters(max_records=1000)
        print(f"Found {len(perimeters)} total perimeters")
        
        # Filter for California 2020 fires
        ca_2020 = [
            p for p in perimeters
            if p.fire_discovery_datetime
            and p.fire_discovery_datetime.year == 2020
            and p.incident_name
            and any(keyword in p.incident_name.lower() 
                   for keyword in ["creek", "california", "ca"])
        ]
        
        print(f"\nFound {len(ca_2020)} California 2020 fires with 'creek' or 'ca':")
        for p in ca_2020[:10]:  # Show first 10
            print(f"  - {p.incident_name} ({p.fire_discovery_datetime.date()}): {p.gis_acres:,.0f} acres")
        
        if len(ca_2020) > 10:
            print(f"  ... and {len(ca_2020) - 10} more")
    
    except Exception as e:
        print(f"NIFC search failed: {e}")
    
    print()
    
    # MTBS search
    print("MTBS Database Search")
    print("-" * 80)
    mtbs = MTBSClient()
    
    try:
        print("Fetching MTBS fires for 2020...")
        fires_2020 = mtbs.get_fires_by_year(year=2020, max_records=1000)
        print(f"Found {len(fires_2020)} fires in 2020")
        
        # Filter for California (look for CA in name or check coordinates)
        ca_fires = [
            f for f in fires_2020
            if f.fire_name
            and ("creek" in f.fire_name.lower() or "ca" in f.fire_name.lower())
        ]
        
        print(f"\nFound {len(ca_fires)} California 2020 fires with 'creek' or 'ca':")
        for f in ca_fires[:10]:
            print(f"  - {f.fire_name}: {f.acres:,.0f} acres")
        
        if len(ca_fires) > 10:
            print(f"  ... and {len(ca_fires) - 10} more")
        
        # Look specifically for Creek Fire
        creek_fires = [f for f in fires_2020 if "creek" in f.fire_name.lower()]
        if creek_fires:
            print(f"\nCreek Fire candidates:")
            for f in creek_fires:
                print(f"  - {f.fire_name}: {f.acres:,.0f} acres, Year: {f.fire_year}")
    
    except Exception as e:
        print(f"MTBS search failed: {e}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    search_2020_california_fires()
