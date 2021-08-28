from threading import Thread
import os
import socket
import argparse
import shlex
import subprocess
import sys
import textwrap

def exec(cmd):
    cmd = cmd.strip()
    print(shlex.split(cmd))
    cmd_dict = shlex.split(cmd)
    if cmd_dict[0] == "cd" and os.name == "nt":
        if len(cmd_dict) == 1:
            get_cur_dir = os.getcwd()
            return get_cur_dir.encode()
        elif cmd_dict[0] and cmd_dict[1] == "..":
            current = os.getcwd()
            cur_splitted = current.split("\\")[:-1]
            #dir_splitted = cur_splitted[:-1]
            dir_fin = "\\".join(cur_splitted)
            #re = f"Changed to {os.getcwd()}"
            os.chdir(dir_fin)
            return f"{os.getcwd()} ".encode()
        else:
            os.chdir(cmd_dict[1])
            #out_dir = f"Changed to {os.getcwd()}"
            return f"{os.getcwd()} ".encode()
    elif cmd_dict[0] == "cd" and os.name == "posix":
        if len(cmd_dict) == 1:
            os.chdir("~/")
            return get_cur_dir.encode()
        elif cmd_dict[0] and cmd_dict[1] == "..":
            current = os.getcwd()
            cur_splitted = current.split("/")[:-1]
            dir_fin = "/"+"/".join(cur_splitted)
            os.chdir(dir_fin)
            return f"{os.getcwd()} ".encode()
        else:
            os.chdir(cmd_dict[1])
            return f"{os.getcwd()} ".encode()

    elif cmd:
        output = subprocess.Popen(shlex.split(cmd),stderr=subprocess.STDOUT,stdout=subprocess.PIPE,shell=True)
        out =  output.stdout.read()
        #print(out)
        if out == b"":
            return b"No Output\n\r"
        else:
            return out
        # return str(out)+str(err)
    return "Command Not Entered"



args = parser.parse_args()

def main(args):
    if args.listen:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.bind((args.target,args.port))
        sock.listen(5)
        print(f"listening on {args.target}:{args.port}")
        try:
            while True:
                client, addr = sock.accept()
                print(addr,"connected")
                handle = Thread(target=client_handle,args=(client,addr))
                handle.start()
        except:
            sock.close()
            print("terminated")
    elif args.upload:
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((args.target,args.port))
            file_buffer = b''
            while True:
                data = sock.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            with open(args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {args.upload}'
            sock.send(message.encode())
        except:
            sock.close()
            sys.exit()

    elif args.execute:
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((args.target,args.port))
            data = args.execute
            sock.send(data.encode())
            recv = sock.recv(4096)
            print(recv.decode())
        except:
            sock.close()
            print("Connection closed successfully")
            sys.exit()
    elif args.shell:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect(("127.0.0.1",43))
        try:
            while True:
                data = input(r"{shell}:> ")
                if data == "":
                    sock.send(b" ")
                else:    
                    sock.send(data.encode())
                recv = sock.recv(10240)
                print(recv.decode())
        except KeyboardInterrupt:
            sock.close()
            print("Connection closed successfully")
            sys.exit()



def client_handle(client_socket,address):
    if args.listen and args.shell:
        addr = address
        try:
            with client_socket as sock:
                while True: 
                    recv = sock.recv(4096) 
                    #print(recv.decode()) 
                    try:
                        sock.send(exec(recv.decode()))
                    except :
                        sock.send(b"\n\r")
        except:
            client_socket.close()
            print("connection closed from",addr)
    elif args.listen:
        addr = address
        try:
            with client_socket as sock:
                #while True: 
                recv = sock.recv(4096) 
                        #print(recv.decode()) 
                try:
                    sock.send(exec(recv.decode()))
                except :
                    sock.send(b"Error Occured")
        except:
            client_socket.close()
            print("connection closed from",addr)
        finally:
            client_socket.close()
            print("connection closed from",addr)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Netcat Tool",formatter_class=
    argparse.RawDescriptionHelpFormatter,epilog=textwrap.dedent("""
    Example:
    netcat.py -t  192.168.1.108 -p 5555 -l -c # command shell
    netcat.py -t  192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
    netcat.py -t  192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
    netcat.py -t  192.168.1.108 -p 5555  #  connect to server
    echo 'ABC' |  ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135"""))
    
    parser.add_argument("-s","--shell",action='store_true',help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen',action='store_true',help='listen')
    parser.add_argument('-p', '--port',type=int, help='specified port')
    parser.add_argument('-t', '--target',help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    main(args)
