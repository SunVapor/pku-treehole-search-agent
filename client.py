"""
PKU Treehole API Client
Handles authentication and API interactions with PKU Treehole.
"""

import enum
import json
import random
import re
import uuid
from http.cookiejar import Cookie

import requests


class TreeHoleWeb(enum.Enum):
    """
    Enum for Treehole web API endpoints.
    """

    OAUTH_LOGIN = "https://iaaa.pku.edu.cn/iaaa/oauthlogin.do"
    REDIR_URL = "https://treehole.pku.edu.cn/cas_iaaa_login?uuid=fc71db5799cf&plat=web"
    SSO_LOGIN = "http://treehole.pku.edu.cn/cas_iaaa_login"
    UN_READ = "https://treehole.pku.edu.cn/api/mail/un_read"
    LOGIN_BY_TOKEN = "https://treehole.pku.edu.cn/api/login_iaaa_check_token"
    LOGIN_BY_MESSAGE = "https://treehole.pku.edu.cn/api/jwt_msg_verify"
    SEND_MESSAGE = "https://treehole.pku.edu.cn/api/jwt_send_msg"


class TreeholeClient:
    """
    Client for interacting with the PKU Treehole API.
    Handles authentication, post/comment retrieval, and search functionality.
    """

    def __init__(self, cookies_file="cookies.json"):
        """
        Initialize the client, set headers, and load cookies if available.
        
        Args:
            cookies_file (str): Path to the cookies file for session persistence.
        """
        self.session = requests.Session()
        self.cookies_file = cookies_file
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
            }
        )
        self.load_cookies()
        # If token exists in cookies, set authorization header
        if "pku_token" in self.session.cookies.keys():
            self.authorization = self.session.cookies.values()[
                self.session.cookies.keys().index("pku_token")
            ]
            self.session.headers.update(
                {"authorization": f"Bearer {self.authorization}"}
            )

    def oauth_login(self, username, password):
        """
        Perform OAuth login with username and password.

        Args:
            username (str): Username for login.
            password (str): Password for login.

        Returns:
            dict: JSON response from the server.
        """
        response = self.session.post(
            TreeHoleWeb.OAUTH_LOGIN.value,
            data={
                "appid": "PKU Helper",
                "userName": username,
                "password": password,
                "randCode": "",
                "smsCode": "",
                "otpCode": "",
                "redirUrl": TreeHoleWeb.REDIR_URL.value,
            },
        )
        response.raise_for_status()
        return response.json()

    def sso_login(self, token):
        """
        Perform SSO login using a token.

        Args:
            token (str): Token for SSO login.

        Returns:
            requests.Response: The HTTP response object.
        """
        rand = str(random.random())
        response = self.session.get(
            TreeHoleWeb.SSO_LOGIN.value,
            params={
                "uuid": str(uuid.uuid4()).split("-")[-1],
                "plat": "web",
                "_rand": rand,
                "token": token,
            },
        )
        response.raise_for_status()
        # Extract token from URL and update session
        self.authorization = re.search(r"token=(.*)", response.url).group(1)
        self.session.cookies.update({"pku_token": self.authorization})
        self.session.headers.update({"authorization": f"Bearer {self.authorization}"})
        return response

    def un_read(self):
        """
        Get unread messages status.

        Returns:
            requests.Response: The HTTP response object.
        """
        response = self.session.get(TreeHoleWeb.UN_READ.value)
        return response

    def login_by_token(self, token):
        """
        Login using a token (e.g., from mobile app).

        Args:
            token (str): Token for login.

        Returns:
            requests.Response: The HTTP response object.
        """
        response = self.session.post(
            TreeHoleWeb.LOGIN_BY_TOKEN.value, data={"token": token}
        )
        response.raise_for_status()
        return response

    def login_by_message(self, code):
        """
        Login using a message code (SMS verification).

        Args:
            code (str): SMS verification code.

        Returns:
            requests.Response: The HTTP response object.
        """
        response = self.session.post(
            TreeHoleWeb.LOGIN_BY_MESSAGE.value, data={"valid_code": code}
        )
        response.raise_for_status()
        return response

    def send_message(self):
        """
        Send an SMS message for verification.

        Returns:
            requests.Response: The HTTP response object.
        """
        response = self.session.post(TreeHoleWeb.SEND_MESSAGE.value)
        response.raise_for_status()
        return response

    def get_post(self, post_id):
        """
        Get a post by its ID.

        Args:
            post_id (int): The post ID.

        Returns:
            dict: JSON response containing the post data.
        """
        response = self.session.get(f"https://treehole.pku.edu.cn/api/pku/{post_id}")
        response.raise_for_status()
        return response.json()

    def get_comment(self, post_id, page=1, limit=15, sort="asc"):
        """
        Get comments for a post.

        Args:
            post_id (int): The post ID.
            page (int): Page number (default: 1).
            limit (int): Number of comments per page (default: 15).
            sort (str): Sort order, 'asc' or 'desc' (default: 'asc').

        Returns:
            dict: JSON response containing the comments data.
        """
        response = self.session.get(
            f"https://treehole.pku.edu.cn/api/pku_comment_v3/{post_id}",
            params={"page": page, "limit": limit, "sort": sort},
        )
        response.raise_for_status()
        return response.json()

    def search_posts(self, keyword, page=1, limit=30, comment_limit=10, **kwargs):
        """
        Search posts by keyword using the Treehole search API.
        
        Based on the actual API: /chapi/api/v3/hole/list_comments
        
        Args:
            keyword (str): The search keyword.
            page (int): Page number (default: 1).
            limit (int): Number of posts per page (default: 30).
            comment_limit (int): Number of comments to include per post (default: 10).
            **kwargs: Additional parameters for the search API.
        
        Returns:
            dict: JSON response containing search results.
            
        Response format:
        {
            "code": 20000,
            "data": {
                "list": [
                    {
                        "pid": 8006047,
                        "text": "帖子内容...",
                        "type": "text",
                        "timestamp": 1770017907,
                        "likenum": 1,
                        "reply": 0,
                        "comment_total": 0,
                        "comment_list": [...],
                        ...
                    },
                    ...
                ],
                "total": 2000
            },
            "message": "success"
        }
        """
        # API endpoint
        url = "https://treehole.pku.edu.cn/chapi/api/v3/hole/list_comments"
        
        # Request parameters
        params = {
            "page": page,
            "limit": limit,
            "comment_limit": comment_limit,
            "keyword": keyword,
        }
        
        # Add any additional parameters
        params.update(kwargs)
        
        # Make the request
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        # Transform the response to match our expected format
        # The API returns {"code": 20000, "data": {"list": [...], "total": ...}}
        # We transform it to {"success": True, "data": {"data": [...], "total": ...}}
        
        if result.get("code") == 20000:
            # Success response
            transformed = {
                "success": True,
                "data": {
                    "data": result["data"]["list"],
                    "total": result["data"].get("total", 0),
                    "page": page,
                    "limit": limit,
                    # Calculate last_page if total is available
                    "last_page": (result["data"].get("total", 0) + limit - 1) // limit if limit > 0 else 1,
                },
                "message": result.get("message", "success")
            }
            
            # Process each post to extract comments properly
            for post in transformed["data"]["data"]:
                # The API already includes comment_list, just rename for consistency
                if "comment_list" in post and post["comment_list"]:
                    post["comments"] = post["comment_list"]
                else:
                    post["comments"] = []
            
            return transformed
        else:
            # Error response
            return {
                "success": False,
                "data": {"data": [], "total": 0, "page": page, "limit": limit, "last_page": 0},
                "message": result.get("message", "Unknown error"),
                "code": result.get("code")
            }

    def save_cookies(self):
        """
        Save session cookies to a file.
        """
        cookies_list = []
        for cookie in self.session.cookies:
            cookie_dict = {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": cookie.expires if cookie.expires else None,
                "secure": cookie.secure,
                "rest": {"HttpOnly": cookie.has_nonstandard_attr("HttpOnly")},
            }
            cookies_list.append(cookie_dict)

        with open(self.cookies_file, "w") as f:
            json.dump(cookies_list, f, indent=4)

    def load_cookies(self):
        """
        Load session cookies from a file, if available.
        """
        try:
            with open(self.cookies_file, "r") as f:
                cookies_list = json.load(f)
            self.session.cookies.clear()
            for cookie_dict in cookies_list:
                cookie = Cookie(
                    version=0,
                    name=cookie_dict["name"],
                    value=cookie_dict["value"],
                    port=None,
                    port_specified=False,
                    domain=cookie_dict["domain"],
                    domain_specified=bool(cookie_dict["domain"]),
                    domain_initial_dot=cookie_dict["domain"].startswith("."),
                    path=cookie_dict["path"],
                    path_specified=bool(cookie_dict["path"]),
                    secure=cookie_dict["secure"],
                    expires=cookie_dict["expires"],
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest=cookie_dict["rest"],
                )
                self.session.cookies.set_cookie(cookie)

        except FileNotFoundError:
            print(f"Cookie file {self.cookies_file} not found. Will login to create new session.")
        except Exception as e:
            print(f"Error loading cookies: {e}")

    def ensure_login(self, username=None, password=None):
        """
        Ensure the client is logged in. If not, perform login.
        
        Args:
            username (str): Username for login.
            password (str): Password for login.
            
        Returns:
            bool: True if logged in successfully, False otherwise.
        """
        response = self.un_read()
        
        # Already logged in
        if response.status_code == 200 and response.json().get("success"):
            return True
        
        # Need to login
        if username and password:
            print("Logging in...")
            token = self.oauth_login(username, password)["token"]
            self.sso_login(token)
            response = self.un_read()
            
            # Handle additional authentication if needed
            while not response.json().get("success"):
                if response.json().get("message") == "请手机短信验证":
                    tmp = input("Send verification code (Y/n): ")
                    if tmp.lower() == "y":
                        self.send_message()
                        code = input("SMS verification code: ")
                        self.login_by_message(code)
                elif response.json().get("message") == "请进行令牌验证":
                    token = input("Mobile token: ")
                    self.login_by_token(token)
                response = self.un_read()
            
            self.save_cookies()
            return True
        else:
            print("Login required but no credentials provided.")
            return False
