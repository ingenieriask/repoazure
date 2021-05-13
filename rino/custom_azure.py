from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    account_name = 'storagerino' # Must be replaced by your <storage_account_name>
    account_key = 'pU9tcVZDotxVdb7OsCa2SQbhUPxQxtJkNQtXW8UQFFuoDp0OYlfxAAZxbjUgeNiknUpBjSyOWGJW6eONIgMhPA==' # Must be replaced by your <storage_account_key>
    azure_container = 'media'
    expiration_secs = None

class AzureStaticStorage(AzureStorage):
    account_name = 'storagerino' # Must be replaced by your storage_account_name
    account_key = 'pU9tcVZDotxVdb7OsCa2SQbhUPxQxtJkNQtXW8UQFFuoDp0OYlfxAAZxbjUgeNiknUpBjSyOWGJW6eONIgMhPA==' # Must be replaced by your <storage_account_key>
    azure_container = 'static'
    expiration_secs = None