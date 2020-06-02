/**
 * Computación Paralela
 * Funciones para las prácticas
 *
 * @author Javier Fresno
 * @version 1.3
 *
 */
#ifndef _CPUTILS_
#define _CPUTILS_

// Includes
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

#ifdef CP_TABLON
#include "cputilstablon.h"
#else
#define	cp_secure_fopen(name) fopen(name,"r")
#endif


/*
 * FUNCIONES
 */


/**
 * Función que devuelve el tiempo
 */
inline double cp_Wtime(){
	struct timeval tv;
	gettimeofday(&tv, (void *) 0);
	return tv.tv_sec + 1.0e-6 * tv.tv_usec;
}


/**
 * Función que lee el tamaño del fichero
 */
inline int cp_FileSize(char * name, size_t * size){

	/* 1. Abrir el fichero */
	FILE * file;

	file = cp_secure_fopen(name);
	if ( file == NULL ) {
		return 0;
	}

	/* 2. Obtener el tamaño */
	fseek( file, 0, SEEK_END );
	*size = (size_t) ftell( file );

	/* 2.1. Comprobar que el ultimo caracter no es un line feed */
	fseek(file, -1, SEEK_CUR);
	if(fgetc(file) == '\n'){
		(*size) -= 1;
	}

	/* 3. Cerrar */
	fclose(file);

	return 1;
}

/**
 * Función que lee el contenido del fichero
 */
inline int cp_FileRead(char * name, void * ptr){

	/* 1. Abrir el fichero */
	FILE * file;

	file = cp_secure_fopen(name);
	if ( file == NULL ) {
		return 0;
	}

	/* 2. Obtener el tamaño */
	fseek( file, 0, SEEK_END );
	size_t size = (size_t) ftell( file );

	/* 2.1. Comprobar que el ultimo caracter no es un line feed */
	fseek(file, -1, SEEK_CUR);
	if(fgetc(file) == '\n'){
		size--;
	}

	fseek( file, 0, SEEK_SET );
	size_t sread = fread(ptr, sizeof(char), size, file);

	if(sread != size) return 0;


	/* 3. Cerrar */
	fclose(file);

	return 1;
}


#endif
