# Security

## Secrets

Secrets include access tokens, API keys, passwords, private keys, and service-role credentials. Treat any value that grants access to an account, project, or data as a secret. Do not commit secrets or paste them into chats, issues, or pull requests. Use environment variables or an approved secret store instead.

If a secret is exposed, revoke or rotate it promptly and update any applications that use it.

## Revoke a Facebook system-user token

In Meta Business Settings, go to **Users -> System users**, select the relevant system user, and use **Revoke tokens**. Create a replacement token if the integration still needs access, update the deployment's secret store, and verify the integration.

## Rotate the Supabase service_role key

In the Supabase Dashboard, open the project and go to **Project Settings -> API Keys** (shown as **API** in some dashboard versions). Rotate or regenerate the `service_role` key. Update the key in every deployment or secret store, redeploy, verify access, and revoke the old key once the new key is working. This key bypasses Row Level Security, so keep it server-side and tightly restricted.