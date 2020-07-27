"""
- CS2911 - 021
- Fall 2019
- Lab 3 - Parser Design
- Names:
    - Stuart Harley
    - Shantosh Reddy

A simple program to receive a message over the "network", using a simple next_byte method
"""


def read_message():
    """
    Reads a message from the "network" and then writes it to a file

    :author: Stuart Harley
    """
    num_lines = read_header()
    message = b''
    for x in range(num_lines):
        message += read_line()
    write_message(message)


def write_message(message):
    """
    Writes a message to a file

    : param bytes object message: The message to be written
    :author: Stuart Harley
    """
    # We are writing raw bytes (plain ASCII text) to the file
    # Since we opened the file in binary mode,
    # you must write a bytes object, not a str.
    with open('message.txt', 'wb') as output_file:
        output_file.write(message)


def next_byte():
    """
    Enter the byte in hexadecimal shorthand
    e.g.
      input a byte: e3

    :return: the byte as a bytes object holding one byte
    :author: Eric Nowac
    """
    msg = input('input a byte: ')
    return int(msg, 16).to_bytes(1, 'big')


def read_header():
    """
    Read the 4-byte header of the message

    :return: the number of lines in the message as a int
    author: Stuart Harley, Shantosh Reddy
    """
    b = next_byte() + next_byte() + next_byte() + next_byte()
    return int.from_bytes(b, 'big')


def read_line():
    """
    Reads 1 line of the message

    :return: the value of the line as a bytes object
    author: Stuart Harley, Shantosh Reddy
    """
    character = next_byte()
    line = character
    while not (character.decode('ASCII') == '\n'):
        character = next_byte()
        line += character
    return line