#!/usr/bin/env python3
"""
Casos de prueba para los requisitos funcionales 1 y 2 del sistema de análisis de riesgo de churn.
"""

import pandas as pd
import numpy as np
import os
import tempfile
import unittest
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Importar la clase principal del módulo
from risk_prediction import FunctionalRequirementsAnalyzer


class TestFunctionalRequirements(unittest.TestCase):
    """Casos de prueba para los requisitos funcionales 1 y 2"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.analyzer = FunctionalRequirementsAnalyzer()
        
        # Crear datos de prueba
        self.test_data = pd.DataFrame({
            'CLIENTE_ANONIMO': ['CLT_001', 'CLT_002', 'CLT_001', 'CLT_003', 'CLT_002'],
            'ANIO': [2023, 2023, 2023, 2023, 2024],
            'MES': [1, 1, 2, 2, 1],
            'VENTAS_KG': [1000, 1500, 1200, 800, 2000]
        })
        
        # Crear archivo temporal para pruebas
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    # ==================== TEST CASES FOR FUNCTIONAL REQUIREMENT 1 ====================
    
    def test_upload_data_success_csv(self):
        """Prueba exitosa de carga de datos CSV"""
        print("\n" + "="*60)
        print("TEST CASE 1.1: Carga exitosa de datos CSV")
        print("="*60)
        
        result = self.analyzer.upload_historical_data(self.temp_file.name)
        
        # Verificaciones
        self.assertTrue(result['success'], "La carga debería ser exitosa")
        self.assertIsNotNone(result['data'], "Los datos deberían estar cargados")
        self.assertEqual(len(result['data']), 5, "Debería tener 5 registros")
        self.assertIn('CLIENTE_ANONIMO', result['data'].columns, "Debería detectar columna de cliente")
        self.assertIn('VENTAS_KG', result['data'].columns, "Debería detectar columna de ventas")
        
        print("✅ TEST PASSED: Carga exitosa de datos CSV")
    
    def test_upload_data_file_not_found(self):
        """Prueba de error cuando el archivo no existe"""
        print("\n" + "="*60)
        print("TEST CASE 1.2: Archivo no encontrado")
        print("="*60)
        
        result = self.analyzer.upload_historical_data('archivo_inexistente.csv')
        
        # Verificaciones
        self.assertFalse(result['success'], "La carga debería fallar")
        self.assertIn('does not exist', result['message'], "Debería indicar que el archivo no existe")
        
        print("✅ TEST PASSED: Error manejado correctamente para archivo no encontrado")
    
    def test_upload_data_invalid_format(self):
        """Prueba de error con formato de archivo inválido"""
        print("\n" + "="*60)
        print("TEST CASE 1.3: Formato de archivo inválido")
        print("="*60)
        
        # Crear archivo con extensión inválida
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        invalid_file.write("test data")
        invalid_file.close()
        
        try:
            result = self.analyzer.upload_historical_data(invalid_file.name)
            
            # Verificaciones
            self.assertFalse(result['success'], "La carga debería fallar")
            self.assertIn('Only CSV or XLSX formats', result['message'], "Debería rechazar formato inválido")
            
            print("✅ TEST PASSED: Error manejado correctamente para formato inválido")
        finally:
            os.unlink(invalid_file.name)
    
    def test_upload_data_missing_required_fields(self):
        """Prueba de error cuando faltan campos requeridos"""
        print("\n" + "="*60)
        print("TEST CASE 1.4: Campos requeridos faltantes")
        print("="*60)
        
        # Crear datos sin campos requeridos
        invalid_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'NOMBRE': ['A', 'B', 'C'],
            'VALOR': [100, 200, 300]
        })
        
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        invalid_data.to_csv(invalid_file.name, index=False)
        invalid_file.close()
        
        try:
            result = self.analyzer.upload_historical_data(invalid_file.name)
            
            # Verificaciones
            self.assertFalse(result['success'], "La carga debería fallar")
            self.assertIn('Required fields not found', result['message'], "Debería indicar campos faltantes")
            self.assertTrue(len(result['validation_errors']) > 0, "Debería tener errores de validación")
            
            print("✅ TEST PASSED: Error manejado correctamente para campos faltantes")
        finally:
            os.unlink(invalid_file.name)
    
    def test_column_detection(self):
        """Prueba de detección automática de columnas"""
        print("\n" + "="*60)
        print("TEST CASE 1.5: Detección automática de columnas")
        print("="*60)
        
        result = self.analyzer.upload_historical_data(self.temp_file.name)
        
        # Verificaciones
        self.assertTrue(result['success'], "La carga debería ser exitosa")
        self.assertEqual(self.analyzer.customer_col, 'CLIENTE_ANONIMO', "Debería detectar columna de cliente")
        self.assertEqual(self.analyzer.quantity_col, 'VENTAS_KG', "Debería detectar columna de cantidad")
        self.assertEqual(self.analyzer.year_col, 'ANIO', "Debería detectar columna de año")
        self.assertEqual(self.analyzer.month_col, 'MES', "Debería detectar columna de mes")
        
        print("✅ TEST PASSED: Detección automática de columnas funcionando")
    
    # ==================== TEST CASES FOR FUNCTIONAL REQUIREMENT 2 ====================
    
    def test_aggregation_monthly_success(self):
        """Prueba exitosa de agregación mensual"""
        print("\n" + "="*60)
        print("TEST CASE 2.1: Agregación mensual exitosa")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Luego agregar
        result = self.analyzer.aggregate_purchases_by_customer_and_period('month')
        
        # Verificaciones
        self.assertTrue(result['success'], "La agregación debería ser exitosa")
        self.assertIsNotNone(result['aggregated_data'], "Debería tener datos agregados")
        self.assertTrue(result['validation_passed'], "La validación de totales debería pasar")
        
        # Verificar estructura de datos agregados
        agg_data = result['aggregated_data']
        expected_columns = ['CLIENTE_ANONIMO', 'period', 'total_kg', 'avg_kg', 'purchase_count', 'total_tons', 'avg_tons']
        for col in expected_columns:
            self.assertIn(col, agg_data.columns, f"Debería tener columna {col}")
        
        # Verificar que los totales coincidan
        original_total = self.test_data['VENTAS_KG'].sum()
        aggregated_total = agg_data['total_kg'].sum()
        self.assertAlmostEqual(original_total, aggregated_total, places=2, 
                              msg="Los totales deberían coincidir")
        
        print("✅ TEST PASSED: Agregación mensual exitosa")
    
    def test_aggregation_quarterly_success(self):
        """Prueba exitosa de agregación trimestral"""
        print("\n" + "="*60)
        print("TEST CASE 2.2: Agregación trimestral exitosa")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Luego agregar
        result = self.analyzer.aggregate_purchases_by_customer_and_period('quarter')
        
        # Verificaciones
        self.assertTrue(result['success'], "La agregación debería ser exitosa")
        self.assertIsNotNone(result['aggregated_data'], "Debería tener datos agregados")
        self.assertTrue(result['validation_passed'], "La validación de totales debería pasar")
        
        print("✅ TEST PASSED: Agregación trimestral exitosa")
    
    def test_aggregation_yearly_success(self):
        """Prueba exitosa de agregación anual"""
        print("\n" + "="*60)
        print("TEST CASE 2.3: Agregación anual exitosa")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Luego agregar
        result = self.analyzer.aggregate_purchases_by_customer_and_period('year')
        
        # Verificaciones
        self.assertTrue(result['success'], "La agregación debería ser exitosa")
        self.assertIsNotNone(result['aggregated_data'], "Debería tener datos agregados")
        self.assertTrue(result['validation_passed'], "La validación de totales debería pasar")
        
        print("✅ TEST PASSED: Agregación anual exitosa")
    
    def test_aggregation_without_data(self):
        """Prueba de error cuando no hay datos cargados"""
        print("\n" + "="*60)
        print("TEST CASE 2.4: Agregación sin datos cargados")
        print("="*60)
        
        # Intentar agregar sin cargar datos primero
        result = self.analyzer.aggregate_purchases_by_customer_and_period('month')
        
        # Verificaciones
        self.assertFalse(result['success'], "La agregación debería fallar")
        self.assertIn('Must load data first', result['message'], "Debería indicar que faltan datos")
        
        print("✅ TEST PASSED: Error manejado correctamente para agregación sin datos")
    
    def test_aggregation_invalid_period(self):
        """Prueba de error con período inválido"""
        print("\n" + "="*60)
        print("TEST CASE 2.5: Período de agregación inválido")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Intentar agregar con período inválido
        result = self.analyzer.aggregate_purchases_by_customer_and_period('invalid_period')
        
        # Verificaciones
        self.assertFalse(result['success'], "La agregación debería fallar")
        self.assertIn('Invalid period', result['message'], "Debería rechazar período inválido")
        
        print("✅ TEST PASSED: Error manejado correctamente para período inválido")
    
    def test_aggregation_metrics_calculation(self):
        """Prueba de cálculo correcto de métricas agregadas"""
        print("\n" + "="*60)
        print("TEST CASE 2.6: Cálculo correcto de métricas")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Luego agregar
        result = self.analyzer.aggregate_purchases_by_customer_and_period('month')
        self.assertTrue(result['success'], "La agregación debería ser exitosa")
        
        agg_data = result['aggregated_data']
        
        # Verificar que las métricas se calculen correctamente
        for _, row in agg_data.iterrows():
            # Verificar conversión a toneladas
            expected_tons = row['total_kg'] / 1000
            self.assertAlmostEqual(row['total_tons'], expected_tons, places=4,
                                  msg="Conversión a toneladas incorrecta")
            
            expected_avg_tons = row['avg_kg'] / 1000
            self.assertAlmostEqual(row['avg_tons'], expected_avg_tons, places=4,
                                  msg="Promedio en toneladas incorrecto")
        
        print("✅ TEST PASSED: Cálculo de métricas correcto")
    
    def test_aggregation_validation_totals(self):
        """Prueba de validación de totales en agregación"""
        print("\n" + "="*60)
        print("TEST CASE 2.7: Validación de totales")
        print("="*60)
        
        # Primero cargar datos
        upload_result = self.analyzer.upload_historical_data(self.temp_file.name)
        self.assertTrue(upload_result['success'], "Datos deben cargarse primero")
        
        # Luego agregar
        result = self.analyzer.aggregate_purchases_by_customer_and_period('month')
        self.assertTrue(result['success'], "La agregación debería ser exitosa")
        
        # Verificar que la validación de totales pase
        self.assertTrue(result['validation_passed'], "La validación de totales debería pasar")
        
        # Verificar que los totales coincidan exactamente
        original_total = self.test_data['VENTAS_KG'].sum()
        aggregated_total = result['aggregated_data']['total_kg'].sum()
        self.assertAlmostEqual(original_total, aggregated_total, places=2,
                              msg="Los totales originales y agregados deben coincidir")
        
        print("✅ TEST PASSED: Validación de totales correcta")


def run_tests():
    """Función para ejecutar todos los casos de prueba"""
    print("=" * 80)
    print("EJECUTANDO CASOS DE PRUEBA PARA REQUISITOS FUNCIONALES 1 Y 2")
    print("=" * 80)
    
    # Crear suite de pruebas
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestFunctionalRequirements)
    
    # Ejecutar pruebas con output detallado
    runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
    result = runner.run(test_suite)
    
    # Mostrar resumen
    print(f"\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Pruebas exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Pruebas fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print("\nPRUEBAS FALLIDAS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nERRORES:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
    
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    """Ejecutar pruebas cuando se ejecuta el archivo directamente"""
    success = run_tests()
    
    if success:
        print("\n🎉 TODOS LOS CASOS DE PRUEBA PASARON EXITOSAMENTE!")
        print("Los requisitos funcionales 1 y 2 están funcionando correctamente.")
        exit(0)
    else:
        print("\n❌ ALGUNOS CASOS DE PRUEBA FALLARON")
        print("Revisa los detalles arriba para identificar los problemas.")
        exit(1)