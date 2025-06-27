# LOL-Analyzer

Este proyecto analiza partidas de League of Legends para estimar qué equipo tiene más probabilidades de ganar, basándose en estadísticas como el KDA promedio, liga y rol de cada jugador.

#Match-Analyzer (Module)

* Es un modulo que analiza que tan probable es que gane un equipo en contra de otro en base a:

  - Rol (Mid, Gj, Top, Adc y Supp)
  - Liga de la persona
  - KDA promedio

* Formula usada:

  ![image](https://github.com/user-attachments/assets/9247e739-9492-4c2f-b0be-4dfb57d3e7ff)
  
  Razon logica de la formula:
  
    - MID (0.25) y JUNGLE (0.22) suelen tener mayor impacto en el mapa: Gankean, rotan, controlan objetivos.
    - ADC (0.21): Aunque dependiente del equipo, es clave en daño tardío.
    - TOP (0.17): Más aislado, pero puede ser determinante si gana.
    - SUPPORT (0.15): Apoya más que carrilea; sin embargo, un buen support cambia el juego (pero de forma menos directa en estadísticas individuales como KDA).

    ![image](https://github.com/user-attachments/assets/3e67e940-9ea0-47e9-a1ef-8e887f5de0b6)

    En la imagen de arriba podemos ver que tanto afecta cada varible de la formula al resultado final.

    | Variable            | Coeficiente | Interpretación clara                                                                                                |
    | ------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
    | **K (Kills)**       | **+1.43**   | Aporta positivamente. Cada kill promedio por jugador suma +1.43 a la fuerza del equipo.                             |
    | **A (Asistencias)** | **+2.61**   | Mucho más importante que las kills. El trabajo en equipo (asistencias) **vale más que matar**.                      |
    | **D (Muertes)**     | **-8.59**   | Fuerte penalización. Más muertes reducen significativamente el valor total del equipo.                              |
    | **Peso\_liga**      | **+5.97**   | tiene **menos impacto** , hay más variabilidad realista (de Iron a Challenger).                                     |
    | **Impacto\_rol**    | **+2.36**   | **El rol tiene un impacto significativo**                                                                           |

  
---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Save-summoner ( Module )

- Sirve para guardar los Summoners.

---------------------------------------------------------------------------------------------------------------------------------------------------------------

#All - Summoners ( Module )

- Muestra todos los Summoners guardados.


---------------------------------------------------------------------------------------------------------------------------------------------------------------

#Match-Saver ( Module )

- Guarda el KDA promedio del jugador para no tener que consultar a la API cada vez que quieras analizar un equipo ( API de Riot con ciertas limitaciones ).

---------------------------------------------------------------------------------------------------------------------------------------------------------------
