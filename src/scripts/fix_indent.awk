{
    # count number of whitespace leading in line
    match($0, "^[[:blank:]]*");
    len = RLENGTH
    num_spaces = RLENGTH * 2;

    spaces = ""
    for (i = 0; i < num_spaces; i++) {
	spaces = spaces " ";
    }

    printf("%s%s\n", spaces, 
	   substr($0, RSTART+RLENGTH, length($0)-RLENGTH))
}