import httpx
import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
from fastapi import HTTPException, status
from typing import Dict, Any, Optional

from database import ThirdServiceConf


class ThirdServiceExecutor:
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    
    def __init__(self, conf: ThirdServiceConf):
        self.conf = conf
    
    def resolve_url(self, runtime_vars: Dict[str, Any]) -> str:
        url = self.conf.base_url
        
        url = self._replace_variables(url, runtime_vars)
        
        url_template = self.conf.config_json.get("url_template", {})
        query_params = url_template.get("query_params", {})
        
        if query_params:
            parsed = urlparse(url)
            existing_params = parse_qs(parsed.query, keep_blank_values=True)
            
            final_params = {}
            for key, value in existing_params.items():
                final_params[key] = value[0] if len(value) == 1 else value
            
            for param_name, var_name in query_params.items():
                if param_name not in final_params and var_name in runtime_vars:
                    final_params[param_name] = runtime_vars[var_name]
            
            if final_params:
                new_query = urlencode(final_params)
                url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
        
        return url
    
    def _replace_variables(self, text: str, runtime_vars: Dict[str, Any]) -> str:
        def replacer(match):
            var_name = match.group(1)
            if var_name in runtime_vars:
                return str(runtime_vars[var_name])
            return match.group(0)
        
        return self.VARIABLE_PATTERN.sub(replacer, text)
    
    def resolve_body(self, runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        body_template = self.conf.config_json.get("body_template", [])
        
        if not isinstance(body_template, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="config_json.body_template must be a list"
            )
        
        body = {}
        
        for mapping in body_template:
            if not isinstance(mapping, dict):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Each body_template item must be a dict"
                )
            
            key = mapping.get("key")
            input_key = mapping.get("input")
            
            if not key or not input_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="body_template items must have 'key' and 'input' fields"
                )
            
            if input_key not in runtime_vars:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required input variable: '{input_key}'"
                )
            
            body[key] = runtime_vars[input_key]
        
        return body
    
    def map_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        response_mapping = self.conf.config_json.get("response_mapping", {})
        
        if not response_mapping:
            return response_data
        
        mapped = {}
        for output_key, source_path in response_mapping.items():
            value = self._get_nested_value(response_data, source_path)
            if value is not None:
                mapped[output_key] = value
        
        mapped["_raw"] = response_data
        return mapped
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    async def execute(self, runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        resolved_url = self.resolve_url(runtime_vars)
        body = self.resolve_body(runtime_vars)
        headers = dict(self.conf.headers_json) if self.conf.headers_json else {}
        
        method = self.conf.http_method.upper()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    params = body if body and len(body) > 0 else None
                    response = await client.request(
                        method=method,
                        url=resolved_url,
                        headers=headers,
                        params=params
                    )
                else:
                    response = await client.request(
                        method=method,
                        url=resolved_url,
                        headers=headers,
                        json=body if body else None
                    )
                
                response.raise_for_status()
                response_data = response.json()
                
                return self.map_response(response_data)
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Third-party service error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to third-party service: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during third-party service execution: {str(e)}"
            )
