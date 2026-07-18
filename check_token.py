import httpx

def main():
    token = "EAAOBFGE978sBRwKO4RLIQqEdjGGZBEKZAzZAUpTVdUqhTWr2I9hrWju2IpQbZB2bWuZBTmEytqdEZAYZCQuaTB4uOCFW4kjre1RkAKU92Lswn3MVuDvqAsc3mREw168nF1jjZBZAkcgh2ZAmFa25Ov86H6vbTjIsqfGaBNkxt4QiHdvtZBNBZAGKOEUSEHgKZBrsly5gofn2ziEWofo9kE3ZCekCaW6MYhoZC8bKW5ZBFUhjIRZA8JneaYyXF2WQWi6rzi58K3OnN5ZCKNNZAU9blZCxxJD8AgU4omtTH9GEyAXCmSzMZBQZDZD"
    
    print("Checking permissions...")
    url = f"https://graph.facebook.com/v20.0/me/permissions?access_token={token}"
    try:
        response = httpx.get(url)
        print("Permissions response:")
        print(response.json())
    except Exception as e:
        print("Failed to query permissions:", e)
        
    print("\nChecking accounts...")
    url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={token}"
    try:
        response = httpx.get(url)
        print("Accounts response:")
        print(response.json())
    except Exception as e:
        print("Failed to query accounts:", e)

if __name__ == "__main__":
    main()
