import logging
from botocore.exceptions import ClientError
from auth import init_client
from bucket.crud import list_buckets, create_bucket, delete_bucket, bucket_exists, show_bucket_tree
from bucket.policy import read_bucket_policy, assign_policy
from bucket.versioning import versioning
from bucket.encryption import set_bucket_encryption, read_bucket_encryption
from bucket.organize import object_per_extension
from host_static.host_web_configuration import source_to_web_host
from object.crud import download_file_and_upload_to_s3, get_objects, upload_local_file
from object.versioning import list_object_versions, rollback_to_version
from my_args import bucket_arguments, object_arguments, host_arguments, quote_arguments
# from host_static import host_web_configuration, host_web_page_files
import argparse
from quote.quote_api import get_quotes, get_random_quote, get_random_quote_by_author, save_to_s3

parser = argparse.ArgumentParser(
    description="CLI program that helps with S3 buckets.",
    prog='main.py',
    epilog='DEMO APP - 2 FOR BTU_AWS'
)

subparsers = parser.add_subparsers(dest='command')

bucket_arguments(subparsers.add_parser("bucket", help="work with Bucket/s"))
object_arguments(subparsers.add_parser("object", help="work with Object/s"))
host_arguments(subparsers.add_parser("host", help="work with Host/s"))
list_bucket = subparsers.add_parser("list_buckets", help="List already created buckets.")
quote_arguments(subparsers.add_parser("quote", help="work with Quote/s"))


def main():
    s3_client = init_client()
    args = parser.parse_args()

    match args.command:

        case "bucket":
            if args.create_bucket == "True":
                if (args.bucket_check == "True") and bucket_exists(s3_client, args.name):
                    parser.error("Bucket already exists")
                if create_bucket(s3_client, args.name, args.region):
                    print(f"Bucket: '{args.name}' successfully created")

            if (args.delete_bucket == "True") and delete_bucket(s3_client, args.name):
                print("Bucket successfully deleted")

            if args.bucket_exists == "True":
                print(f"Bucket exists: {bucket_exists(s3_client, args.name)}")

            if args.read_policy == "True":
                print(read_bucket_policy(s3_client, args.name))

            if (args.list_objects == "True"):
                get_objects(s3_client, args.name)

            if args.assign_read_policy == "True":
                assign_policy(s3_client, "public_read_policy", args.name)

            if args.assign_missing_policy == "True":
                assign_policy(s3_client, "multiple_policy", args.name)

            if args.bucket_encryption == "True":
                if set_bucket_encryption(s3_client, args.name):
                    print("Encryption set")

            if args.read_bucket_encryption == "True":
                print(read_bucket_encryption(s3_client, args.name))

            if args.versioning == "True":
                versioning(s3_client, args.name, True)
                print("Enabled versioning on bucket %s." % args.name)

            if args.versioning == "False":
                versioning(s3_client, args.name, False)
                print("Disabled versioning on bucket %s." % args.name)

            if args.organize_bucket:
                object_per_extension(s3_client, args.name)
                print("organized")

            if args.show_bucket_tree:
              show_bucket_tree(s3_client, args.name, '', True)
              

        case "object":
            if args.object_link:
                if (args.download_upload == "True"):
                    print(download_file_and_upload_to_s3(s3_client, args.bucket_name, args.object_link, args.keep_file_name))

            if args.local_object:
                print(upload_local_file(s3_client, args.bucket_name, args.local_object, args.keep_file_name, args.upload_type))

            if args.name:
                if args.list_versions:
                    list_object_versions(s3_client, args.bucket_name, args.name)

                if args.roll_back_to:
                    rollback_to_version(s3_client, args.bucket_name, args.name, args.roll_back_to)

        case "list_buckets":
            buckets = list_buckets(s3_client)
            if buckets:
                for bucket in buckets['Buckets']:
                    print(f' Name:  {bucket["Name"]}')

        case "host":
            if args.source is not None:
                source_to_web_host(s3_client, args)
            
        case "quote":
            quotes = get_quotes()
            quote = None
            if args.inspire is None:
                quote = get_random_quote(quotes)
                print(f'"{quote["text"]}"\n- {quote["author"]}')
            elif isinstance(args.inspire, str):
                quote = get_random_quote_by_author(args.inspire, quotes)
                print(f'"{quote["text"]}"\n- {quote["author"]}')

            if (args.save == True):
                print(save_to_s3(s3_client, args.bucket_name, quote))


if __name__ == "__main__":
    try:
        main()
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            logging.warning("Bucket already exists! Using it.")
        else:
            logging.error(error)
    except ValueError as error:
        logging.error(error)
