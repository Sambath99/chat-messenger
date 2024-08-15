from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import unquote_plus
from jinja2 import Environment, FileSystemLoader

# Configure Jinja2 environment
env = Environment(loader=FileSystemLoader('templates'))

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Check if username is already stored in browser cookies
            stored_username = None
            if 'Cookie' in self.headers:
                cookies = self.headers['Cookie'].split('; ')
                for cookie in cookies:
                    if cookie.startswith('username='):
                        stored_username = cookie.split('=')[1]

            if not stored_username:
                # If username is not found in cookies, send the HTML form to enter username
                template = env.get_template('index.html')
                self.wfile.write(template.render().encode('utf-8'))
            else:
                # If username is found, display the chat interface
                template = env.get_template('chat.html')
                self.wfile.write(template.render(username=stored_username).encode('utf-8'))
        elif self.path == "/messages":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Load existing messages from JSON file
            try:
                with open('messages.json', 'r') as f:
                    messages = json.load(f)
            except FileNotFoundError:
                messages = []

            # Return messages as JSON response
            self.wfile.write(json.dumps(messages).encode('utf-8'))
        elif self.path == "/admin":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Render admin page
            template = env.get_template('admin.html')
            self.wfile.write(template.render().encode('utf-8'))
        elif self.path == "/total-users":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Load existing users from JSON file
            try:
                with open('users.json', 'r') as f:
                    users = json.load(f)
            except FileNotFoundError:
                users = []

            # Return total users count and usernames as JSON response
            total_users = len(users)
            usernames = [user['username'] for user in users]
            response_data = {'totalUsers': total_users, 'usernames': usernames}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404: Page not found')

    def do_POST(self):
        if self.path == "/submit":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            message_data = post_data.split('&')
            username = unquote_plus(message_data[0].split('=')[1]).replace('+', ' ')  # Decode URL encoded username and replace '+' with ' '
            message = unquote_plus(message_data[1].split('=')[1])  # Decode URL encoded message

            # Load existing messages from JSON file
            try:
                with open('messages.json', 'r') as f:
                    messages = json.load(f)
            except FileNotFoundError:
                messages = []

            # Append new message with actual username to messages list
            messages.append({'username': username, 'message': message})

            # Save messages back to JSON file
            with open('messages.json', 'w') as f:
                json.dump(messages, f, indent=4)

            # Redirect back to the chat page after submitting message
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        elif self.path == "/":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            username = post_data.split('=')[1]

            # Set username in response header as a cookie to save it in browser cookies
            self.send_response(303)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'username={username}; Path=/')
            self.end_headers()

            # Save username to users.json
            try:
                with open('users.json', 'r') as f:
                    users = json.load(f)
            except FileNotFoundError:
                users = []

            users.append({'username': username})

            with open('users.json', 'w') as f:
                json.dump(users, f, indent=4)
        elif self.path == "/clear-messages":
            # Clear message history
            with open('messages.json', 'w') as f:
                json.dump([], f)
            self.send_response(200)
            self.end_headers()
        elif self.path == "/delete-users":
            # Delete all registered users
            with open('users.json', 'w') as f:
                json.dump([], f)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404: Page not found')

if __name__ == '__main__':
    httpd = HTTPServer(('', 8000), MyHandler)
    print('Server started on localhost:8000...')
    httpd.serve_forever()
