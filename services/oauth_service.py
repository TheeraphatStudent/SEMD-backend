from typing import Dict, Optional
import httpx
import secrets
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config.settings import settings
from database import User


class OAuthService:

    def __init__(self):
        pass

    @classmethod
    async def initiate_github_device_flow(cls) -> Dict[str, any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://github.com/login/device/code',
                    headers={
                        'Accept': 'application/json'
                    },
                    data={
                        'client_id': settings.github_client_id,
                        'scope': 'read:user user:email'
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail='Failed to initiate GitHub device flow'
                    )

                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"GitHub API error: {str(e)}"
            )

    @classmethod
    async def poll_github_device_flow(cls, device_code: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://github.com/login/oauth/access_token',
                    headers={
                        'Accept': 'application/json'
                    },
                    data={
                        'client_id': settings.github_client_id,
                        'device_code': device_code,
                        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
                    }
                )

                data = response.json()

                if 'error' in data:
                    if data['error'] == 'authorization_pending':
                        return None
                    elif data['error'] == 'slow_down':
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail='Polling too frequently'
                        )
                    elif data['error'] == 'expired_token':
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Device code expired'
                        )
                    elif data['error'] == 'access_denied':
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail='User denied authorization'
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"OAuth error: {data['error']}"
                        )

                return data.get('access_token')
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"GitHub API error: {str(e)}"
            )

    @classmethod
    def generate_github_authorization_url(cls, state: str) -> str:
        base_url = 'https://github.com/login/oauth/authorize'
        params = {
            'client_id': settings.github_client_id,
            'redirect_uri': settings.github_redirect_uri,
            'scope': 'read:user%20user:email',
            'state': state
        }
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    @classmethod
    async def exchange_github_code(cls, code: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://github.com/login/oauth/access_token',
                    headers={
                        'Accept': 'application/json'
                    },
                    data={
                        'client_id': settings.github_client_id,
                        'client_secret': settings.github_client_secret,
                        'code': code,
                        'redirect_uri': settings.github_redirect_uri
                    }
                )

                data = response.json()

                if 'error' in data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"GitHub OAuth error: {data.get('error_description', data['error'])}"
                    )

                return data.get('access_token')
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"GitHub API error: {str(e)}"
            )

    @classmethod
    async def get_github_user_info(cls, access_token: str) -> Dict[str, str]:
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f"Bearer {access_token}",
                    'Accept': 'application/json'
                }

                response = await client.get(
                    'https://api.github.com/user',
                    headers=headers
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Invalid GitHub token'
                    )

                user_data = response.json()

                email_response = await client.get(
                    'https://api.github.com/user/emails',
                    headers=headers
                )

                email = user_data.get('email')
                if not email and email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next(
                        (e['email'] for e in emails if e.get('primary')),
                        None
                    )
                    if primary_email:
                        email = primary_email

                return {
                    'id': str(user_data.get('id')),
                    'email': email or f"{user_data.get('login')}@github.user",
                    'name': user_data.get('name') or user_data.get('login')
                }
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"GitHub API error: {str(e)}"
            )

    @classmethod
    async def exchange_github_token(cls, token: str) -> Dict[str, str]:
        return await cls.get_github_user_info(token)

    @classmethod
    def generate_google_authorization_url(cls, state: str) -> str:
        scopes = [
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]

        base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'client_id': settings.google_client_id,
            'redirect_uri': settings.google_redirect_uri,
            'response_type': 'code',
            'scope': '%20'.join(scopes),
            'state': state,
            'access_type': 'offline'
        }
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    @classmethod
    async def exchange_google_code(cls, code: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'client_id': settings.google_client_id,
                        'client_secret': settings.google_client_secret,
                        'code': code,
                        'grant_type': 'authorization_code',
                        'redirect_uri': settings.google_redirect_uri
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Failed to exchange Google authorization code'
                    )

                data = response.json()
                return data.get('access_token')
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google API error: {str(e)}"
            )

    @classmethod
    async def get_google_user_info(cls, access_token: str) -> Dict[str, str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f"Bearer {access_token}"}
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Invalid Google token'
                    )

                user_data = response.json()

                return {
                    'id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'avatar_url': user_data.get('picture')
                }
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google API error: {str(e)}"
            )

    @classmethod
    async def exchange_google_token(cls, token: str) -> Dict[str, str]:
        return await cls.get_google_user_info(token)

    @classmethod
    def upsert_oauth_user(
        cls,
        provider: str,
        user_info: Dict[str, str],
        db: Session
    ) -> User:
        print(user_info)

        if provider == 'github':
            user = db.query(User).filter(User.gh_id == user_info['id']).first()
        elif provider == 'google':
            user = db.query(User).filter(User.gg_id == user_info['id']).first()
        else:
            user = None

        if user:
            db.commit()
            db.refresh(user)
            return user

        existing_user = db.query(User).filter(
            User.email == user_info['email']).first()
        if existing_user:
            if provider == 'github':
                existing_user.gh_id = user_info['id']
                existing_user.profile_img_uri = user_info['avatar_url']
            elif provider == 'google':
                existing_user.gg_id = user_info['id']
                existing_user.profile_img_uri = user_info['avatar_url']
            db.commit()
            db.refresh(existing_user)
            return existing_user

        username = user_info['email'].split('@')[0]
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1

        new_user = User(
            username=username,
            email=user_info['email'],
            full_name=user_info['name'],
            password_hash='',
            role='MEMBER'
        )

        if provider == 'github':
            new_user.gh_id = user_info['id']
            new_user.profile_img_uri = user_info['avatar_url']
        elif provider == 'google':
            new_user.gg_id = user_info['id']
            new_user.profile_img_uri = user_info['avatar_url']

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


oauth_service = OAuthService()
