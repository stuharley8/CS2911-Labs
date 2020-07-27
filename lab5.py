"""
- CS2911 - 0NN
- Fall 2017
- Lab 5
- Names:
  - Stuart Harley
  - Shanthosh Reddy

A simple HTTP client
"""

# import the "socket" module -- not using "from socket import *" in order to selectively use items with "socket." prefix
import socket

# import the "regular expressions" module
import re


def main():
    """
    Tests the client on a variety of resources
    """

    # These resource request should result in "Content-Length" data transfer
    get_http_resource('http://msoe.us/CS/cs1.1chart.png', 'cs1.1chart.png')

    # this resource request should result in "chunked" data transfer
    get_http_resource('http://msoe.us/CS/', 'index.html')

    # If you find fun examples of chunked or Content-Length pages, please share them with us!


def get_http_resource(url, file_name):
    """
    Get an HTTP resource from a server
           Parse the URL and call function to actually make the request.

    :param url: full URL of the resource to get
    :param file_name: name of file in which to store the retrieved resource

    (do not modify this function)
    """

    # Parse the URL into its component parts using a regular expression.
    url_match = re.search('http://([^/:]*)(:\d*)?(/.*)', url)
    url_match_groups = url_match.groups() if url_match else []
    #    print 'url_match_groups=',url_match_groups
    if len(url_match_groups) == 3:
        host_name = url_match_groups[0]
        host_port = int(url_match_groups[1][1:]) if url_match_groups[1] else 80
        host_resource = url_match_groups[2]
        print('host name = {0}, port = {1}, resource = {2}'.format(host_name, host_port, host_resource))
        status_string = make_http_request(host_name.encode(), host_port, host_resource.encode(), file_name)
        print('get_http_resource: URL="{0}", status="{1}"'.format(url, status_string))
    else:
        print('get_http_resource: URL parse failed, request not sent')


def make_http_request(host, port, resource, file_name):
    """
    Get an HTTP resource from a server

    :param bytes host: the ASCII domain name or IP address of the server machine (i.e., host) to connect to
    :param int port: port number to connect to on server host
    :param bytes resource: the ASCII path/name of resource to get. This is everything in the URL after the domain name,
           including the first /.
    :param file_name: string (str) containing name of file in which to store the retrieved resource
    :return: the status code
    :rtype: int
    :author: Stuart Harley, Shanthosh Reddy
    """
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((host, port))
    send_request(host, resource, data_socket)

    status_line = get_next_header(data_socket)
    status_code = get_status_code(status_line)

    headers = b''
    while b'\r\n\r\n' not in headers:
        headers += get_next_header(data_socket)
    body_length = interpret_body_length(headers)
    data = b''
    if body_length == 'chunked':
        data = interpret_chunked(data_socket)
    elif body_length.isnumeric():
        data = interpret_content_length(data_socket, int(body_length))
    else:
        print('Neither chuncked or content-length')
    write_message(data, file_name)
    return status_code


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


def send_request(host, resource, socket):
    """
    Create and send a HTTP request for the resource
    :param host: hostname
    :param resource: resource
    :param socket: the socket
    :author: Stuart Harley
    """
    request = b'GET ' + resource + b' HTTP/1.1\r\nHost: ' + host + b'\r\n\r\n'
    socket.sendall(request)


def get_next_header(data_socket):
    """
    Read the next header from the HTTP response

    :param data_socket: the socket to read from
    :return: the next header as a byte object
    :rtype: byte object
    :author: Stuart Harley
    """
    header = b''
    while b'\r\n' not in header:
        header += next_byte(data_socket)
    return header


def get_status_code(header):
    """
    This should be called after the first call of get_next_header()
    Gets the status code from the status line

    :param header: the status line
    :return: the status code as an int
    :rtype: int
    :author: Stuart Harley, Shanthosh Reddy
    """
    index = header.index(b' ')
    status_code = header[index + 1:index + 4]
    return status_code.decode('ASCII')


def interpret_body_length(headers):
    """
    Interprets whether the message is content-length or chunked

    Content length is stored in the response as 'Content-Length: <length>'
    <length> is the length in decimal number of octets
    Otherwise is will be 'Transfer-Encoding: chunked'

    :param headers: the headers as a byte object
    :return: the status code as a str. Either 'chunked' or the actual number of octets
    :rtype: str
    :author: Stuart Harley, Shanthosh Reddy
    """
    headers = headers.decode('ASCII')
    if 'Transfer-Encoding: chunked' in headers:
        return 'chunked'
    else:
        index = headers.index('Content-Length:')
        length_and_rest_of_headers = headers[index + 16:]
        index = length_and_rest_of_headers.index('\r')
        length = length_and_rest_of_headers[:index]
        return length


def interpret_content_length(data_socket, body_length):
    """
    Decodes the body of the message

    :param data_socket: the socket to read from
    :param body_length: the length of the body as an int
    :return: the body of the message as a bytes object
    :rtype: bytes object
    :author: Stuart Harley, Shanthosh Reddy
    """
    data = b''
    for x in range(body_length):
        data += next_byte(data_socket)
    return data


def interpret_chunked(data_socket):
    """
    Interprets the chunked message and returns it as a byte object

    :param data_socket: the socket to read from
    :return: the data as a bytes object
    :rtype: bytes object
    :author: Stuart Harley, Shanthosh Reddy
    """
    chunk_length = get_chunk_length(data_socket)
    chunk_data = b''
    while not chunk_length == 0:
        for x in range(chunk_length):
            chunk_data += next_byte(data_socket)
        next_byte(data_socket)  # Clears the next CR LF
        next_byte(data_socket)
        chunk_length = get_chunk_length(data_socket)
    return chunk_data


def get_chunk_length(data_socket):
    """
    Reads the chunk length and returns it as an int
    :param data_socket: the socket
    :return: the chunk length as an int
    :rtype: int
    :author: Stuart Harley, Shanthosh Reddy
    """
    chunk_length = next_byte(data_socket)
    while b'\r\n' not in chunk_length:
        chunk_length += next_byte(data_socket)
    chunk_length = chunk_length[:-2]
    return int(chunk_length, 16)


def write_message(data, filename):
    """
    Writes a message to a file

    :param bytes object data: The data to be written
    :param str filename: the filename
    :author: Stuart Harley
    """
    # We are writing raw bytes (plain ASCII text) to the file
    # Since we opened the file in binary mode,
    # you must write a bytes object, not a str.
    with open(filename, 'wb') as output_file:
        output_file.write(data)


main()
