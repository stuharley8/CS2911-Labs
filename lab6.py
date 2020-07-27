"""
- CS2911 - 021
- Fall 2019
- Lab 6
- Names:
  - Stuart Harley
  - Shanthosh Reddy

A simple HTTP server
"""

import socket
import re
import threading
import os
import mimetypes
import datetime


def main():
    """ Start the server """
    http_server_setup(8080)


def http_server_setup(port):
    """
    Start the HTTP server
    - Open the listening socket
    - Accept connections and spawn processes to handle requests

    :param port: listening port number
    """

    num_connections = 10
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_address = ('', port)
    server_socket.bind(listen_address)
    server_socket.listen(num_connections)
    try:
        while True:
            request_socket, request_address = server_socket.accept()
            print('connection from {0} {1}'.format(request_address[0], request_address[1]))
            # Create a new thread, and set up the handle_request method and its argument (in a tuple)
            request_handler = threading.Thread(target=handle_request, args=(request_socket,))
            # Start the request handler thread.
            request_handler.start()
            # handle_request(request_socket) to be used for testing, comment out previous 2 lines
            # Just for information, display the running threads (including this main one)
            print('threads: ', threading.enumerate())
    # Set up so a Ctrl-C should terminate the server; this may have some problems on Windows
    except KeyboardInterrupt:
        print("HTTP server exiting . . .")
        print('threads: ', threading.enumerate())
        server_socket.close()


def next_byte(data_socket):
    """
    Read the next byte from the socket data_socket.

    Read the next byte from the sender, received over the network.
    If the byte has not yet arrived, this method blocks (waits)
      until the byte arrives.
    If the sender is done sending and is waiting for your response, this method blocks indefinitely.

    :param data_socket: The socket to read from. The data_socket argument should be an open tcp
                        data connection (either a client socket or a server data socket), not a tcp
                        server's listening socket.
    :return: the next byte, as a bytes object with a single byte in it
    """
    return data_socket.recv(1)


def get_next_header(data_socket):
    """
    Read the next header from the HTTP request

    :param data_socket: the socket to read from
    :return: the next header as a bytes object
    :rtype: bytes object
    :author: Stuart Harley
    """
    header = b''
    while b'\r\n' not in header:
        header += next_byte(data_socket)
    return header


def parse_headers(data_socket):
    """
    Reads through the headers of the request and returns the headers
    as str objects stored in a dictionary

    :param: data_socket: the socket to read from
    :return: a dictionary containing the headers
    :rtype: dictionary
    :author: Stuart Harley, Shanthosh Reddy
    """
    headers = {}
    header = get_next_header(data_socket)
    while header != b'\r\n':
        header = header.decode('ASCII')
        split_header = header.split(': ')
        headers[split_header[0]] = split_header[1]
        header = get_next_header(data_socket)
    return headers


def parse_request_line(data_socket):
    """
    Reads the request line of the request and returns the url

    :param: data_socket: the socket to read from
    :return: the url as a bytes object
    :rtype: bytes object
    :author: Shanthosh Reddy
    """
    request_line = b''
    while b'\r\n' not in request_line:
        request_line += next_byte(data_socket)
    request_line = request_line.split()
    return request_line[1]


def parse_request(data_socket):
    """
    Parses through the request line and headers of the request. Prints out the headers
    to verify the request is being handled correctly since we will not need the headers further.
    Returns the url from the request line.

    :param: data_socket: the socket to read from
    :return: the url from the request line as a bytes object
    :rtype: bytes object
    :author: Stuart Harley
    """
    request_url = parse_request_line(data_socket)
    headers = parse_headers(data_socket)
    for k, v in headers.items():
        print(k + ": " + v)
    return request_url


def generate_status_line(status_code):
    """
    Generates the status line of the HTTP response

    :param: status_code: the status code as a bytes object
    :return: the status line of the HTTP response as a bytes object
    :rtype: bytes object
    :author: Stuart Harley, Shanthosh Reddy
    """
    status_line = b'HTTP/1.1 ' + status_code
    if status_code == b'200':
        status_line += b' OK\r\n'
    elif status_code == b'404':
        status_line += b' Not Found\r\n'
    return status_line


def generate_response_headers(file_path):
    """
    Generates the response headers of the HTTP response. Includes a Date header,
    a Connection header indicating a non-persistent connection, a Content-Type
    header with the appropriate MIME type, and a Content-Length header to specify
    the size of the resource being returned (if there is one).

    :param: file_path: the file path
    :return: the response headers of the HTTP response in a dictionary, where the key
    is the header name as a byte object, and the value is the value as a bytes object
    :rtype: dictionary
    :author: Stuart Harley, Shanthosh Reddy
    """
    response_headers = {}
    timestamp = datetime.datetime.utcnow()
    timestring = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
    #                               Sun, 06 Nov 1994 08:49:37 GMT
    response_headers[b'Date: '] = timestring.encode('ASCII') + b'\r\n'
    response_headers[b'Connection: '] = b'close\r\n'
    response_headers[b'Content-Type: '] = str(get_mime_type(file_path)).encode('ASCII') + b'\r\n'
    response_headers[b'Content-Length: '] = str(get_file_size(file_path)).encode('ASCII') + b'\r\n'
    return response_headers


def send_response(status_line, response_headers, response_body, data_socket):
    """
    Sends the entire HTTP response consisting of the status_line, headers, and body

    :param status_line: the status line as a bytes object
    :param response_headers: the response headers as a dictionary containing bytes objects
    :param response_body: the body as a bytes object
    :param data_socket: the socket
    :return: None
    :author: Stuart Harley
    """
    response = status_line
    for k, v in response_headers.items():
        response += k + v
    response += b'\r\n'
    response += response_body
    data_socket.sendall(response)


def parse_file(file_path):
    """
    Opens the requested file for the program to use

    :param file_path: the file path to open
    :return: an open file
    :author: Stuart Harley
    """
    msg = b''
    with open(file_path, 'rb') as file_object:
        msg += file_object.read()
    return msg


def handle_request(request_socket):
    """
    Handle a single HTTP request, running on a newly started thread.

    Closes request socket after sending response.

    Should include a response header indicating NO persistent connection

    :param request_socket: socket representing TCP connection from the HTTP client_socket
    :return: None
    :authors: Stuart Harley, Shanthosh Reddy
    """
    url = (parse_request(request_socket).decode('ASCII'))[1:]
    response_headers = {}
    response_body = b''
    status_code = b'200'
    try:
        response_headers = generate_response_headers(url)
        response_body = parse_file(url)
    except:
        status_code = b'404'
    status_line = generate_status_line(status_code)
    send_response(status_line, response_headers, response_body, request_socket)
    request_socket.close()


# ** Do not modify code below this line.  You should add additional helper methods above this line.

# Utility functions
# You may use these functions to simplify your code.


def get_mime_type(file_path):
    """
    Try to guess the MIME type of a file (resource), given its path (primarily its file extension)

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If successful in guessing the MIME type, a string representing the content type, such as 'text/html'
             Otherwise, None
    :rtype: int or None
    """

    mime_type_and_encoding = mimetypes.guess_type(file_path)
    mime_type = mime_type_and_encoding[0]
    return mime_type


def get_file_size(file_path):
    """
    Try to get the size of a file (resource) as number of bytes, given its path

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If file_path designates a normal file, an integer value representing the the file size in bytes
             Otherwise (no such file, or path is not a file), None
    :rtype: int or None
    """

    # Initially, assume file does not exist
    file_size = None
    if os.path.isfile(file_path):
        file_size = os.stat(file_path).st_size
    return file_size


main()

# acmesystems.it/python_http
