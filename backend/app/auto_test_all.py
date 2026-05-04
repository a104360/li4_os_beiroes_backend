import auto_test_eventos_facade
import auto_test_gestao_facade
import auto_test_boleia_facade

if __name__ == '__main__':
    auto_test_gestao_facade.run_integrated_test()
    auto_test_eventos_facade.run_integrated_test()
    auto_test_boleia_facade.run_logistica_test()