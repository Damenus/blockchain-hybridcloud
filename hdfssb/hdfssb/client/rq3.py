import subprocess
import os
import ast
import hashlib
import json

import simplejson as simplejson


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
    # drop-rate > repair-symbols-rate
    # private      public       ilosć bloków
    # procent bloków do pirvate
    # (blocks - (blocks*drop_rate)) / nodes > repair-symbols-rate

    # launch your python2 script using bash
    encode = """
    ./python-libraptorq/rq \
    --debug \
    encode \
    -s{s} \
    -m200 \
    --repair-symbols-rate 1 \
    --drop-rate 0.5 \
    {path_src} \
    {path_dst}
    """.format(s=s, path_src=file_name, path_dst=file_name+'.enc')

    decode = """
    ./python-libraptorq/rq \
    --debug \
    decode \
    {path_src} \
    {path_dst}
    """.format(path_src='dd/enc', path_dst='dd/dec')
    #""".format(path_src=file_name+'.enc', path_dst=file_name+'.dec')

    process = subprocess.Popen(encode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script

    # "needed: >(\d*),"
    # dla małych plików jak mp3
    # file_encoded_map = os.read_fiel as map

    # with open(file_name+'.enc', 'r') as myfile:
    #     data = myfile.read()
    #
    # mapa = ast.literal_eval(data)

    with open(file_name + '.enc', 'r') as myfile:
        mapa = json.load(myfile)


    user = 'ddarczuk'
    #file_name
    #hash

    i = 0
    for block in mapa['symbols']:
        # hash_object = hashlib.sha1(bytes(block[1]))
        # hex_dig = hash_object.hexdigest()
        # print(hex_dig)

        name = user + '-' + file_name + '-' + str(i)
        i += 1
        # f = open('dd/'+name, "w+")
        # f.write(str(block))
        # f.close()
        with open('dd/'+name, "w+") as json_file:
            json.dump(block, json_file)

    del mapa['symbols']
    # f = open('dd/head', "w+")
    # f.write(str(mapa))
    # f.close()
    with open('dd2/head', "w+") as json_file:
        json.dump(mapa, json_file)

    # with open('dd/head', 'r') as myfile:
    #     data = myfile.read()
    #
    # mapa = ast.literal_eval(data)
    with open('dd2/head', 'r') as myfile:
        mapa = json.load(myfile)

    mapa['symbols'] = []
    print(mapa)

    for filename in os.listdir('dd'):
        # with open('dd/'+filename, 'r') as myfile:
        #     data = myfile.read()
        with open('dd/'+filename, 'r') as myfile:
            data = json.load(myfile)
            mapa['symbols'].append(data)

    # f = open('dd/enc', "w+")
    # f.write(str(mapa))
    # f.close()
    with open('dd/enc', "w+") as json_file:
        json.dump(mapa, json_file)

    # now write output to a file
    twitterDataFile = open("dd/enc2", "w")
    # magic happens here to make it pretty-printed
    twitterDataFile.write(simplejson.dumps(mapa, indent=4, sort_keys=True))
    twitterDataFile.close()

    process = subprocess.Popen(decode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script


if __name__ == "__main__":
    main()
