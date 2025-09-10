#!/usr/bin/env python3
"""
Script para ejecutar los casos de prueba de los requisitos funcionales 1 y 2
"""

import sys
import os

# Agregar el directorio actual al path para importar el módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_functional_requirements import run_tests

if __name__ == "__main__":
    print("=" * 80)
    print("EJECUTANDO CASOS DE PRUEBA PARA REQUISITOS FUNCIONALES 1 Y 2")
    print("=" * 80)
    
    success = run_tests()
    
    if success:
        print("\n🎉 TODOS LOS CASOS DE PRUEBA PASARON EXITOSAMENTE!")
        print("Los requisitos funcionales 1 y 2 están funcionando correctamente.")
        sys.exit(0)
    else:
        print("\n❌ ALGUNOS CASOS DE PRUEBA FALLARON")
        print("Revisa los detalles arriba para identificar los problemas.")
        sys.exit(1)