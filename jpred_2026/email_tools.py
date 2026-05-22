def obfuscate_email(email):
    """Obfuscate email to show first 3 chars of username and first 3 of domain, e.g., stu***@gma***"""
    if '@' in email:
        username, domain = email.split('@', 1)
        # Obfuscate username
        if len(username) <= 3:
            obfuscated_user = username + '***'
        else:
            obfuscated_user = username[:3] + '***'
        # Obfuscate domain
        if len(domain) <= 3:
            obfuscated_domain = domain + '***'
        else:
            obfuscated_domain = domain[:3] + '***'
        return f"{obfuscated_user}@{obfuscated_domain}"
    else:
        return email[:3] + '***'
