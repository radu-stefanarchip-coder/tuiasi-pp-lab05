#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <regex.h>
 
// Aceeasi cheie folosita in Python  
#define CHEIE_COADA  0x48540001
#define TIP_MESAJ    1L
#define DIM_MESAJ    1024
#define DIM_BUFFER   65536   // buffer acumulare HTML  
#define FISIER_IESIRE "output.html"
 

struct mesaj_buffer {
    long tip;
    char text[DIM_MESAJ];
};
 
/*
  valideaza_html
  Verifica daca sirul contine cel putin un tag HTML valid (<tag> sau </tag>).
  Returneaza 1 daca validarea trece
 */
int valideaza_html(const char *html) {
    regex_t regex;
    int rezultat;
    const char *pattern = "<[a-zA-Z][a-zA-Z0-9]*[^>]*>";
 
    if (regcomp(&regex, pattern, REG_EXTENDED) != 0) {
        fprintf(stderr, "[receiver] Eroare la compilarea regex.\n");
        return 0;
    }
 
    rezultat = regexec(&regex, html, 0, NULL, 0);
    regfree(&regex);
 
    return (rezultat == 0) ? 1 : 0;
}
 
int main(void) {
    int id_coada;
    struct mesaj_buffer mesaj;
    char buffer[DIM_BUFFER];
    int offset = 0;
 
    printf("[receiver] Pornit. Astept mesaje pe cheia 0x%X...\n", CHEIE_COADA);
 

    id_coada = msgget((key_t)CHEIE_COADA, 0666 | IPC_CREAT);
    if (id_coada == -1) {
        perror("[receiver] msgget esuat");
        return EXIT_FAILURE;
    }
 
    memset(buffer, 0, sizeof(buffer));
 

    while (1) {
        memset(mesaj.text, 0, DIM_MESAJ);
 
        if (msgrcv(id_coada, &mesaj, DIM_MESAJ, TIP_MESAJ, 0) == -1) {
            perror("[receiver] msgrcv esuat");
            break;
        }
 

        if (strcmp(mesaj.text, "__END__") == 0) {
            printf("[receiver] Transmisie completa.\n");
            break;
        }
 
        // Acumuleaza in buffer
        int lungime_chunk = (int)strlen(mesaj.text);
        if (offset + lungime_chunk < DIM_BUFFER - 1) {
            memcpy(buffer + offset, mesaj.text, lungime_chunk);
            offset += lungime_chunk;
        } else {
            fprintf(stderr, "[receiver] Buffer depasit, HTML prea mare.\n");
            break;
        }
    }
 
    if (offset == 0) {
        fprintf(stderr, "[receiver] Nu s-a primit niciun continut.\n");
        return EXIT_FAILURE;
    }
 
  
    printf("[receiver] Validez HTML-ul cu regex...\n");
    if (!valideaza_html(buffer)) {
        fprintf(stderr, "[receiver] Validare esuata: continutul nu pare a fi HTML valid.\n");
        return EXIT_FAILURE;
    }
    printf("[receiver] Validare reusita.\n");
 
    // Scriere
    FILE *fisier = fopen(FISIER_IESIRE, "w");
    if (!fisier) {
        perror("[receiver] Nu s-a putut deschide fisierul de iesire");
        return EXIT_FAILURE;
    }
 
    fputs(buffer, fisier);
    fclose(fisier);
 
    printf("[receiver] HTML scris in '%s'.\n", FISIER_IESIRE);
 
    // Distruge coada
    msgctl(id_coada, IPC_RMID, NULL);
    printf("[receiver] Coada de mesaje distrusa.\n");
 
    return EXIT_SUCCESS;
}