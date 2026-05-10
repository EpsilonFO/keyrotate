PROVIDERS: dict[str, dict[str, str | None]] = {
    "anthropic": {
        "name": "Anthropic",
        "rotation_url": "https://console.anthropic.com/settings/keys",
    },
    "openai": {
        "name": "OpenAI",
        "rotation_url": "https://platform.openai.com/api-keys",
    },
    "mistral": {
        "name": "Mistral",
        "rotation_url": "https://console.mistral.ai/api-keys",
    },
    "supabase": {
        "name": "Supabase",
        "rotation_url": "https://app.supabase.com/project/_/settings/api",
    },
    "aws": {
        "name": "AWS IAM",
        "rotation_url": "https://console.aws.amazon.com/iam/home#/security_credentials",
    },
    "gcp": {
        "name": "Google Cloud",
        "rotation_url": "https://console.cloud.google.com/iam-admin/serviceaccounts",
    },
    "stripe": {
        "name": "Stripe",
        "rotation_url": "https://dashboard.stripe.com/apikeys",
    },
    "github": {
        "name": "GitHub",
        "rotation_url": "https://github.com/settings/tokens",
    },
    "vercel": {
        "name": "Vercel",
        "rotation_url": "https://vercel.com/account/tokens",
    },
    "cloudflare": {
        "name": "Cloudflare",
        "rotation_url": "https://dash.cloudflare.com/profile/api-tokens",
    },
    "resend": {
        "name": "Resend",
        "rotation_url": "https://resend.com/api-keys",
    },
    "other": {
        "name": "Other",
        "rotation_url": None,
    },
}


def default_rotation_url(provider: str) -> str | None:
    return PROVIDERS.get(provider, {}).get("rotation_url")
