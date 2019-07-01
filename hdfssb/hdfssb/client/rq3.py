import subprocess
import os


def main():
    # s = min(file_size - 1, 65528) # 65528 is 2^16 - 8, max uint16_t
    # s = s - s mod 8
    file_name = 'SampleAudio_0.7mb.mp3'
    file_size = os.path.getsize(file_name)
    s = min(file_size - 1, 65528)
    s = s - s % 8

    ###
    # liczba nodów
    # liczba nodów które potrzebne jest
    #

    # launch your python2 script using bash
    encode = """
    /home/ddarczuk/PycharmProjects/blockchain-hybridcloud/python-libraptorq/rq \
    --debug \
    encode \
    -s{s} \
    -m200 \
    --repair-symbols-rate 0.1 \
    --drop-rate 0.1 \
    {path_src} \
    {path_dst}
    """.format(s=s, path_src=file_name, path_dst=file_name+'.enc')

    decode = """
    /home/ddarczuk/PycharmProjects/blockchain-hybridcloud/python-libraptorq/rq \
    --debug \
    decode \
    {path_src} \
    {path_dst}
    """.format(path_src=file_name+'.enc', path_dst=file_name+'.dec')

    process = subprocess.Popen(encode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script

    process = subprocess.Popen(decode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script


if __name__ == "__main__":
    main()
