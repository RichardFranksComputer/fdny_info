# Console commands

Commands were found via:
    - `strings FDNYFIREFIGHTER.exe | grep -C 50 -i playsnd`
    - decompiling .exe in Ghidra and searching `playsnd`

Each method gave a slightly different list of cammands. [console_full_list.txt](console_full_list.txt) contains the combined list.

- [console_decomp.c](console_decomp.c) contains raw decompiled code containing all console variables.
- [console_decomp_list.txt](console_decomp_list.txt] contains variables extracted from the conosle
- [console_exe_strings_list.txt](console_exe_strings_list.txt) contains variables extracted from `strings` command