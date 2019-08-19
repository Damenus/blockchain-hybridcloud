import pathlib
import re
import subprocess
import os
import csv
import matplotlib.pyplot as plt

file_name = "photo.png"

owner_folder = './tmp_send/'
folder = owner_folder + file_name + '/'
pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

# 1. Encode file by raptor

# s = min(file_size - 1, 65528) # 65528 is 2^16 - 8, max uint16_t
# s = s - s mod 8
file_size = os.path.getsize(file_name)
s = min(file_size - 1, 65528)
s = s - (s % 8)

###
# liczba nodów
# liczba nodów które potrzebne jest
# drop-rate > repair-symbols-rate
# private      public       ilosć bloków
# procent bloków do pirvate
# (blocks - (blocks*drop_rate)) / nodes > repair-symbols-rate

#  ./python-libraptorq/rq --debug encode -s1600 -m200 --repair-symbols-rate 1 --drop-rate 0.5 README.rst README.rst.enc

# launch your python2 script using bash
repair_symbols_rate = 1

table_stat = []
plt_secure_group = []


plt.figure(1)

plt_symbols = ['s-', '>-', 'v-', '<-', '^-', 'o-']
row = 0
for sefty in [0, 0.2, 0.4, 0.6, 0.8, 1]:
    plt_x = []
    plt_x_percent = []
    plt_y = []
    plt_y_prc = []
    plt_y_private_nodes = []
    plt_y_percent_public = []
    plt_y_percent_private = []

    for repair_symbols_rate in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
                                1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2]:
        encode = """./python-libraptorq/rq \
           --debug \
           encode \
           -s{s} \
           -m200 \
           --repair-symbols-rate {repair_symbols_rate} \
           {path_src} \
           {path_dst}""".format(s=s, repair_symbols_rate=repair_symbols_rate, path_src=file_name,
                                path_dst=owner_folder + file_name + '.enc')  # .split("\n")  # --drop-rate 0.5 \

        process = subprocess.Popen(encode, stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()  # receive output from the python2 script

        # "needed: >(\d*),"
        # dla małych plików jak mp3
        # file_encoded_map = os.read_fiel as map

        # x = re.search(r'(?P<symbols>\d*) symbols \(needed: >(?P<needed>\d*)', output.decode("utf-8"))
        # needed = int(x['needed'])
        # symbols = int(x['symbols'])
        x = re.search(r'(?P<symbols>\d*) symbols \(needed: >(?P<needed>\d*)', output.decode("utf-8"))
        symbols = int(x.group(1))
        needed = int(x.group(2))

        security = int(sefty * needed)
        max_number_public_node = needed - security
        max_number_private_node = symbols - needed + security

        print(symbols, needed, max_number_public_node, max_number_private_node)
        # print(symbols, needed/symbols, max_number_public_node/symbols, max_number_private_node/symbols)

        if repair_symbols_rate == 0:
            for r in range(1, needed):
                if r < max_number_public_node:
                    plt_y.append(r)
                else:
                    plt_y.append(max_number_public_node)

                if max_number_public_node - r >= 0:
                    plt_y_private_nodes.append(max_number_public_node - r)
                else:
                    plt_y_private_nodes.append(r - max_number_public_node)

                plt_x.append(r)

        table_stat.append([str(sefty),
                           str(symbols),
                           str(needed),
                           str(max_number_public_node),
                           str(max_number_private_node),
                           str(needed / symbols),
                           str(max_number_public_node / symbols),
                           str(max_number_private_node / symbols)])

        plt_x.append(symbols)
        plt_x_percent.append(symbols)
        plt_y.append(max_number_public_node)
        plt_y_prc.append(max_number_private_node)
        plt_y_private_nodes.append(max_number_private_node)

        plt_y_percent_public.append(max_number_public_node / symbols)
        plt_y_percent_private.append(max_number_private_node / symbols)

        # plt_y_form_one_to_needed_public = []
        # plt_y_form_one_to_needed_private = []
        # plt_x_form_one_to_needed = []

    ax1 = plt.subplot(511)
    line, = ax1.plot(plt_x,  plt_y, plt_symbols[row])
    line.set_label(str(sefty*100) + '%')
    line.set_dashes([2, 2, 10, 2])
    ax1.set_xlim([1, symbols])
    ax1.set_ylim([0, symbols+1])
    plt.ylabel('Liczba bloków na prywatnym serwerze')
    plt.xlabel('Liczba wszystkich bloków')
    ax1.legend()
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    ax2 = plt.subplot(512)
    line, = ax2.plot(plt_x,  plt_y_private_nodes, plt_symbols[row])
    line.set_label(str(sefty*100) + '%')
    ax2.set_xlim([1, symbols])
    ax2.set_ylim([0, symbols+1])
    ax2.legend()
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    ax3 = plt.subplot(513)
    line, = ax3.plot(plt_x_percent, plt_y_percent_public, plt_symbols[row])
    line.set_label(str(sefty*100) + '%')
    ax3.set_xlim([needed-1, symbols])
    ax3.legend()
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    ax4 = plt.subplot(514)
    line, = ax4.plot(plt_x_percent, plt_y_percent_private, plt_symbols[row])
    line.set_label(str(sefty*100) + '%')
    ax4.set_xlim([needed - 1, symbols])
    ax4.legend()
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    ax5 = plt.subplot(515)
    ax5.plot(plt_x_percent, plt_y_prc, plt_symbols[row])


    row += 1

plt.show()

with open('secure.csv', 'w') as writeFile:
    writer = csv.writer(writeFile)
    writer.writerows(table_stat)
