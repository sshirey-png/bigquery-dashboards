"""
Deploy SR2/PMAP2 Dashboard to Google Cloud Storage
Creates a static website that can be shared via URL
"""

from google.cloud import storage
import os

def deploy_dashboard(bucket_name, html_file='index.html'):
    """
    Deploy the dashboard to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket (must be globally unique)
        html_file: Path to the HTML file to deploy
    """

    print("=" * 60)
    print("Deploying Dashboard to Google Cloud Storage")
    print("=" * 60)
    print()

    # Initialize storage client
    storage_client = storage.Client()

    # Check if bucket exists, create if not
    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"✓ Using existing bucket: {bucket_name}")
    except:
        print(f"Creating new bucket: {bucket_name}")
        bucket = storage_client.create_bucket(
            bucket_name,
            location="US"
        )
        print(f"✓ Bucket created: {bucket_name}")

        # Make bucket public for website hosting
        bucket.make_public(recursive=True, future=True)

    # Upload the HTML file
    print(f"\nUploading {html_file}...")
    blob = bucket.blob('index.html')
    blob.upload_from_filename(html_file)

    # Set content type and make publicly readable
    blob.content_type = 'text/html'
    blob.cache_control = 'no-cache, max-age=0'
    blob.make_public()
    blob.patch()

    print("✓ File uploaded successfully")

    # Configure bucket for website hosting
    print("\nConfiguring bucket for static website hosting...")
    bucket.configure_website(main_page_suffix='index.html')

    # Get the public URL
    public_url = f"https://storage.googleapis.com/{bucket_name}/index.html"

    print("\n" + "=" * 60)
    print("✓ Deployment Complete!")
    print("=" * 60)
    print(f"\nYour dashboard is now live at:")
    print(f"\n  {public_url}")
    print(f"\nShare this URL with your team!")
    print("\nNote: Anyone with this link can view the dashboard.")
    print("=" * 60)

    return public_url

def main():
    """Main execution function."""

    print("\n** Important: The bucket name must be globally unique **")
    print("Suggestion: Use something like 'yourorg-sr2-pmap2-dashboard'\n")

    bucket_name = input("Enter a bucket name: ").strip().lower()

    if not bucket_name:
        print("Error: Bucket name cannot be empty")
        return

    # Check if index.html exists
    if not os.path.exists('index.html'):
        print("\nError: index.html not found in current directory")
        print("Please run this script from the bigquery_dashboards folder")
        return

    try:
        deploy_dashboard(bucket_name)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you've run: gcloud auth application-default login")
        print("  2. If bucket name is taken, try a different name")
        print("  3. Ensure you have Storage Admin permissions in your GCP project")

if __name__ == "__main__":
    main()
