"""C/C++ knowledge for CreoXEngine — Phase 1, slice 1.

Separate module next to the 12 cybersecurity topics: the cyber topics in
creox_engine.py are untouched, so nothing that works today breaks.
Answers are written from the two cheat sheets already in the workspace
(C Language CheatSheet.pdf, C++ Cheatsheet.pdf) and each answer carries
its source, so a student can check it instead of just trusting it.
The engine stays honest: outside cyber + C/C++ it still says it does
not know.
"""
from __future__ import annotations

# topic -> (keywords, answer). Same matching shape as the cyber topics:
# whole-word keywords, multi-word phrases matched as substrings.
_CCPP_TOPICS: dict[str, tuple[list[str], str]] = {
    "c pointer": (
        ["pointer", "pointers", "dereference", "address of"],
        "Pointer in C: a pointer is a variable that stores the address of "
        "another variable. Example: int x = 10; int *ptr = &x; — here &x is "
        "the address of x, and *ptr (dereference) gives the value 10. "
        "Writing *ptr = 20; changes x itself to 20. Pointers are also how C "
        "does call by reference, for example a swap function taking "
        "int *a, int *b. Source: C Language CheatSheet.pdf (section 7, Pointers).",
    ),
    "c data types": (
        ["data type", "data types", "variable", "variables", "int ", "char ",
         "float", "double", "sizeof"],
        "C data types: char is 1 byte, int is typically 4 bytes, float is "
        "4 bytes and double is 8 bytes. Example: char c = 'A'; int i = 42; "
        "float f = 3.14f; double d = 3.14159; Use sizeof(int) to check a "
        "type's size on your machine. Source: C Language CheatSheet.pdf "
        "(section 2, Data Types & Variables).",
    ),
    "c arrays": (
        ["array", "arrays"],
        "Arrays in C: int arr[5] = {1, 2, 3, 4, 5}; The number of elements "
        "is sizeof(arr) / sizeof(arr[0]). Walk through it with a for loop "
        "over size_t i from 0 to size - 1. Source: C Language CheatSheet.pdf "
        "(section 5, Arrays).",
    ),
    "c strings": (
        ["string", "strings", "strlen", "strcpy", "strcat", "strcmp"],
        "Strings in C: a string is a char array ending in a null character, "
        "and you need #include <string.h>. Useful functions: strlen (length), "
        "strcpy (copy), strcat (concatenate), strcmp (compare — returns 0 "
        "when equal). Prefer the n-versions (strncpy, strncat, strncmp) to "
        "avoid overflows. Source: C Language CheatSheet.pdf (section 6, Strings).",
    ),
    "c functions": (
        ["function", "functions", "call by reference", "swap"],
        "Functions in C: declare first (int add(int a, int b);), define the "
        "body (return a + b;), then call it (int sum = add(5, 10);). C "
        "passes arguments by value by default; to let a function change the "
        "caller's variable, pass a pointer — call by reference, as in a swap "
        "function taking int *a, int *b. Source: C Language CheatSheet.pdf "
        "(section 8, Functions).",
    ),
    "c structures": (
        ["structure", "struct", "typedef"],
        "Structures in C: a struct groups different types together, for "
        "example struct Student { char name[50]; int age; }; then "
        "struct Student s1 = {\"John\", 20}; and access fields as s1.name, "
        "s1.age. typedef creates an alias for a type, so you can write just "
        "Student s1; afterwards. Source: C Language CheatSheet.pdf "
        "(section 9, Structures).",
    ),
    "c file io": (
        ["file", "fopen", "fprintf", "fgets", "fclose"],
        "File I/O in C: #include <stdio.h>, then FILE *fp = "
        "fopen(\"data.txt\", \"w\"); to write, fprintf(fp, ...) to write, and "
        "fclose(fp) when done. To read, open with \"r\" and loop with "
        "fgets(line, sizeof(line), fp). Always close the file. "
        "Source: C Language CheatSheet.pdf (section 10, File I/O).",
    ),
    "c memory": (
        ["malloc", "calloc", "realloc", "free", "dynamic allocation",
         "memory allocation"],
        "Memory management in C: #include <stdlib.h>. malloc reserves memory "
        "(int *arr = (int *)malloc(5 * sizeof(int));), calloc does the same "
        "but zero-initialised, realloc resizes an existing block, and "
        "free(arr) releases it. Always check for NULL after malloc and "
        "always free what you allocated. Source: C Language CheatSheet.pdf "
        "(section 13, Memory Management).",
    ),
    "c loops": (
        ["loop", "loops", "for loop", "while loop", "do while", "do-while",
         "if else", "switch", "control flow"],
        "Control flow in C: if-else chooses between branches, switch "
        "chooses by a value (remember break in each case), for loops repeat "
        "a known number of times (for (int i = 0; i < 5; i++) ...), while "
        "loops repeat while a condition holds, and do-while runs the body "
        "at least once before checking. Source: C Language CheatSheet.pdf "
        "(section 4, Control Flow).",
    ),
    "c compile": (
        ["compile", "gcc", "printf", "scanf", "format specifier"],
        "Compiling and I/O in C: compile with gcc program.c -o program, "
        "then run ./program; add -Wall to see warnings (recommended). "
        "printf prints (%d for int, %f for float/double, %c for char, %s "
        "for string) and scanf reads input — scanf(\"%d\", &num); needs the "
        "& address. Source: C Language CheatSheet.pdf (sections 1, 3, 14).",
    ),
    "cpp basics": (
        ["cout", "cin", "iostream", "namespace"],
        "C++ basics: #include <iostream> and using namespace std; then "
        "cout << prints to the console and cin >> reads input. Boilerplate: "
        "int main() { cout << \"Hello\"; return 0; }. A namespace groups "
        "names to avoid conflicts — namespace A { int x = 10; } is used as "
        "A::x. Source: C++ Cheatsheet.pdf (Basics, Namespaces).",
    ),
    "cpp class": (
        ["class", "object", "constructor"],
        "Classes and objects in C++: a class is a blueprint, an object is "
        "an instance of it. Example: class Car { public: string brand; "
        "int year; void drive() { cout << \"Driving\"; } }; then Car c1; "
        "c1.brand = \"BMW\"; c1.drive(); A constructor has the same name as "
        "the class and runs when the object is created — Car(string b, "
        "int y) sets brand and year. Source: C++ Cheatsheet.pdf "
        "(Object-Oriented Programming, Class & Object, Constructor).",
    ),
    "cpp inheritance": (
        ["inheritance", "derived", "base class"],
        "Inheritance in C++: a derived class reuses a base class. Example: "
        "class Vehicle { public: void honk() { cout << \"Beep!\"; } }; then "
        "class Car : public Vehicle { }; — a Car object can call obj.honk(); "
        "because it inherited it. Source: C++ Cheatsheet.pdf (Inheritance).",
    ),
    "cpp polymorphism": (
        ["polymorphism", "virtual", "override"],
        "Polymorphism in C++: a virtual function in a base class can be "
        "overridden in a derived class. Example: Animal has virtual "
        "void sound(), Dog overrides it to print \"Bark\", and Animal* a = "
        "new Dog(); a->sound(); prints Bark — the call follows the real "
        "object, not the pointer type. Source: C++ Cheatsheet.pdf "
        "(Polymorphism, Virtual Functions).",
    ),
    "cpp reference": (
        ["reference", "nullptr"],
        "References and pointers in C++: a reference is an alias — "
        "int a = 10; int &ref = a; then ref = 20; makes a become 20. A "
        "pointer holds an address instead: int *ptr = &x; and *ptr reads "
        "the value. Use nullptr for null pointers in C++11 and later, and "
        "-> to access members through a pointer. Source: C++ Cheatsheet.pdf "
        "(References, Pointers).",
    ),
    "cpp stl": (
        ["stl", "vector", "map", "set", "stack"],
        "STL in C++ (Standard Template Library): ready-made containers and "
        "algorithms — vector (dynamic array), map (key-value pairs), set "
        "(unique sorted values), stack (last-in, first-out), and more. "
        "Source: C++ Cheatsheet.pdf (Additional Key Concepts, STL).",
    ),
    "cpp templates": (
        ["template", "templates", "generic"],
        "Templates in C++: generic programming — one function works for many "
        "types. Example: template <typename T> T add(T a, T b) { return "
        "a + b; } works for int, double, and other types without rewriting "
        "the function. Source: C++ Cheatsheet.pdf (Templates).",
    ),
    "cpp exception": (
        ["exception", "try catch", "throw"],
        "Exception handling in C++: code that may fail goes in try, errors "
        "are signalled with throw, and caught with catch. Example: try { "
        "throw runtime_error(\"Error occurred\"); } catch (exception &e) { "
        "cout << \"Caught: \" << e.what(); }. Source: C++ Cheatsheet.pdf "
        "(Exception Handling).",
    ),
    "cpp file handling": (
        ["fstream", "ofstream", "ifstream", "getline"],
        "File handling in C++: #include <fstream>. ofstream writes "
        "(ofstream myFile(\"test.txt\"); myFile << \"Hello\"; myFile.close();) "
        "and ifstream reads (ifstream readFile(\"test.txt\"); while "
        "(getline(readFile, line)) { cout << line; }). Modes include "
        "ios::in, ios::out, ios::app and ios::binary. Source: C++ "
        "Cheatsheet.pdf (File Handling).",
    ),
}
