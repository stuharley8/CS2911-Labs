"""
- CS2911 - 021
- Fall 2019
- Lab 7
- Names:
  - Stuart Harley
  - Shanthosh Reddy

A Trivial File Transfer Protocol Server
"""

# import modules -- not using "from socket import *" in order to selectively use items with "socket." prefix
import socket
import os
import math

# Helpful constants used by TFTP
TFTP_PORT = 69
TFTP_BLOCK_SIZE = 512
MAX_UDP_PACKET_SIZE = 65536


def main():
    """
    Processes a single TFTP request

    :author: Stuart Harley, Shanthosh Reddy
    """

    client_socket = socket_setup()
    print("Server is ready to receive a request")

    message = client_socket.recvfrom(MAX_UDP_PACKET_SIZE)
    address = message[1]
    message = message[0]
    op_code = get_op_code(message)
    filename = get_filename(message).decode('ASCII')
    mode = get_mode(message)
    if op_code != b'\x00\x01':
        return
    file_block_count = get_file_block_count(filename)
    block_count = 1
    while block_count <= file_block_count:
        send_data_block(client_socket, filename, address, block_count)
        new_message = client_socket.recvfrom(MAX_UDP_PACKET_SIZE)
        new_message = new_message[0]
        new_op_code = get_op_code(new_message)
        if new_op_code == b'\x00\x04':
            block_num = get_block_num(new_message)
            if block_num != block_count.to_bytes(2, 'big'):
                block_count -= 1
            block_count += 1
        elif new_op_code == b'\x00\x05':
            print(get_error_message(new_message))
            break

    client_socket.close()


def get_file_block_count(filename):
    """
    Determines the number of TFTP blocks for the given file
    :param filename: THe name of the file
    :return: The number of TFTP blocks for the file or -1 if the file does not exist
    """
    try:
        # Use the OS call to get the file size
        #   This function throws an exception if the file doesn't exist
        file_size = os.stat(filename).st_size
        return math.ceil(file_size / TFTP_BLOCK_SIZE)
    except:
        return -1


def get_file_block(filename, block_number):
    """
    Get the file block data for the given file and block number
    :param filename: The name of the file to read
    :param block_number: The block number (1 based)
    :return: The data contents (as a bytes object) of the file block
    """
    file = open(filename, 'rb')
    block_byte_offset = (block_number - 1) * TFTP_BLOCK_SIZE
    file.seek(block_byte_offset)
    block_data = file.read(TFTP_BLOCK_SIZE)
    file.close()
    return block_data


def put_file_block(filename, block_data, block_number):
    """
    Writes a block of data to the given file
    :param filename: The name of the file to save the block to
    :param block_data: The bytes object containing the block data
    :param block_number: The block number (1 based)
    :return: Nothing
    """
    file = open(filename, 'wb')
    block_byte_offset = (block_number - 1) * TFTP_BLOCK_SIZE
    file.seek(block_byte_offset)
    file.write(block_data)
    file.close()


def socket_setup():
    """
    Sets up a UDP socket to listen on the TFTP port
    :return: The created socket
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', TFTP_PORT))
    return s


####################################################
# Write additional helper functions starting here  #
####################################################


def get_op_code(message):
    """
    Gets the op code from the request

    :param message: the request message
    :return: the op code as a bytes object
    :rtype: bytes object
    :author: Stuart Harley
    """
    return message[:2]


def get_filename(message):
    """
    Gets the filename from the request

    :param message: the request message
    :return: the filename as a bytes object
    :rtype: bytes object
    :author: Stuart Harley
    """
    message = message[2:]
    index = message.index(b'\x00')
    return message[:index]


def get_mode(message):
    """
    Gets the mode from the request

    :param message: the request message
    :return: the mode as a bytes object
    :rtype: bytes object
    :author: Stuart Harley
    """
    message = message[2:]
    index = message.index(b'\x00')
    message = message[index + 1:]
    index = message.index(b'\x00')
    return message[:index]


def get_block_num(message):
    """
    Gets the block number from an ack

    :param message: the ack message
    :return: the block number as a bytes object
    :rtype: bytes object
    """
    return message[2:]


def send_data_block(data_socket, filename, address, block_count):
    """
    Gets the next block of data and then sends that block of data with op code 3

    :param data_socket: the socket to send to
    :param filename: the filename
    :param address: the address
    :param block_count: the current block number
    :return: void
    :author: Stuart Harley
    """
    block_data = get_file_block(filename, block_count)
    data_socket.sendto(b'\x00\x03' + block_count.to_bytes(2, "big") + block_data, address)


def get_error_message(message):
    """
    Takes in an error message and returns the string ErrMsg

    :param message: the error message
    :return: the error message as a str
    :rtype: str
    :author: Stuart Harley, Shanthosh Reddy
    """
    return message[4:-1].decode('ASCII')


main()
