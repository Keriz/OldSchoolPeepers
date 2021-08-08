from skidl import *
import subprocess


def place_part_inline(pin_net, part):
    out_net = Net()
    part[1] += out_net
    part[2] += pin_net
    return out_net


def add_decoupling(nets, part):
    for n in nets:
        p = part()
        p[1] += n
        p[2] += Net.get('GND')


class LedPanel():
    def __init__(self):
        ic_74hc595 = Part('74xx', '74HC595', dest=TEMPLATE, footprint='glabs_misc:TSSOP-16_slim',
                          PN='SN74HC595DB-MF', Manf='Texas Instruments',)
        ic_tlc59025 = Part('glabs_misc', 'TLC59025', dest=TEMPLATE, footprint='glabs_misc:SSOP-24_slim',
                           PN='TLC59025IDBQR', Manf='Texas Instruments')
        connector = Part('Connector_Generic_Shielded', 'Conn_01x20_Shielded', dest=TEMPLATE,
                         footprint='glabs_conn:FH12-20S-0.5SVA(54)', PN='FH12-20S-0.5SVA(54)', Manf='Hirose Electric Co Ltd')
        c_100uF = Part('Device', 'CP1', dest=TEMPLATE,
                       footprint='Capacitor_SMD:CP_Elec_5x3.9', PN='UWX1C101MCL1GB', Manf='Nichicon')
        c_100nF = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0402_1005Metric',
                       value='100nF', PN='CL05B104KP5NNNC', Manf='Samsung Electro-Mechanics')
        cap = Part('Device', 'C', dest=TEMPLATE,
                   footprint='Capacitor_SMD:C_0402_1005Metric')
        rgb = Part('Device', 'LED_ARGB', dest=TEMPLATE,
                   footprint='glabs_led:led_rbag_2020', PN='FM-B2020RGBA-HG', Manf='Foshan NationStar Optoelectronics')
        res = Part('Device', 'R', dest=TEMPLATE,
                   footprint='Resistor_SMD:R_0402_1005Metric')
        pmos = Part('Device', 'Q_PMOS_GSD', dest=TEMPLATE,
                    footprint='Package_TO_SOT_SMD:SOT-23', PN='PJ2301-AU_R1_000A1', Manf='PANJIT International')

        # constant_current_led_driver = [
        #    ic_tlc59025(), ic_tlc59025(), ic_tlc59025()]
        shift_registers = ic_74hc595() * 6
        cc_drivers_r = ic_tlc59025() * 3
        cc_drivers_g = ic_tlc59025() * 3
        cc_drivers_b = ic_tlc59025() * 3
        leds_rbag = 48 * 48 * rgb()
        mosfets = 48 * pmos()
        out_connector = connector()
        in_connector = connector()

        led_bus_common_nets = [Net('sclk'),
                               Net('latch'),
                               Net('blank'),
                               Net('row_latch'),
                               Net('row_blank')]

        led_panel_bus = Bus('bus_conn_in', Net('dr'),
                            Net('dg'),
                            Net('db'),
                            *led_bus_common_nets, Net('row_data'))

        _led_panel_bus = Bus('bus_conn_out', Net('_dr'),
                             Net('_dg'),
                             Net('_db'),
                             *led_bus_common_nets, Net('row_dout'))

        # decoupling_caps = [Part('', value='100nF') for i in range(10)]
        #  decoupling_caps_power == []

        VCC = Net('VCC')
        GND = Net('GND')

        # Output Capacitors
        VCC += place_part_inline(GND, c_100uF())
        VCC += place_part_inline(GND, c_100uF())

        out_connector[1, 2, 9, 13, 17] += GND
        out_connector[3, 4, 5, 18, 19, 20] += VCC

        in_connector[1, 2, 9, 13, 17] += GND
        in_connector[3, 4, 5, 18, 19, 20] += VCC

        in_connector['SH'] += GND
        out_connector['SH'] += GND

       # (Net('dr'), Net('dg'), Net('db'), Net('sckl'), Net('latch'), Net('blank'), Net('row_data'), Net('row_latch'), Net('row_blank')) += led_panel_bus
        in_connector[6, 7, 8, 10, 11, 12, 14, 15, 16] += led_panel_bus

       # Net('_dr'), Net('_dg'), Net('_db'), Net('sckl'), Net('latch'), Net('blank'), Net('row_dout'), Net('row_latch'), Net('row_blank') += _led_panel_bus
        out_connector[6, 7, 8, 10, 11, 12, 14, 15, 16] += _led_panel_bus

        for i in range(48):
            mosfets[i][2] += VCC
            for j in range(48):
                leds_rbag[i*48+j] += mosfets[i][3]

        shift_registers[0][14] = led_panel_bus['row_data']

        for i in range(0, 5):
            # SD0 -> SDI
            shift_registers[i][9] += shift_registers[i+1][14]

        for i in range(6):
            shift_registers[i][11] += led_panel_bus['sclk']
            shift_registers[i][8] += GND
            shift_registers[i][16] += VCC
            shift_registers[i][12] += led_panel_bus['row_latch']
            shift_registers[i][13] += led_panel_bus['row_blank']
            shift_registers[i][10] += VCC

            add_decoupling(shift_registers[i][16], c_100nF)

            for j in range(7):
                pin_offset = 1
                # gate to SR outputs
                mosfets[i*8+j][1] += shift_registers[i][j+pin_offset]
            # pin Qa
            mosfets[i*8+7][1] += shift_registers[i][15]

        shift_registers[5][9] += _led_panel_bus['row_dout']

        cc_drivers_r[0][2] += led_panel_bus['dr']
        cc_drivers_g[0][2] += led_panel_bus['dg']
        cc_drivers_b[0][2] += led_panel_bus['db']

        for i in range(0, 2):
            # SDI0 -> SDI
            cc_drivers_r[i][22] += cc_drivers_r[i+1][2]
            cc_drivers_g[i][22] += cc_drivers_g[i+1][2]
            cc_drivers_b[i][22] += cc_drivers_b[i+1][2]

        for i in range(3):
            cc_drivers_r[i][1] += GND
            cc_drivers_g[i][1] += GND
            cc_drivers_b[i][1] += GND

            cc_drivers_r[i][24] += VCC
            cc_drivers_g[i][24] += VCC
            cc_drivers_b[i][24] += VCC

            cc_drivers_r[i][3] += led_panel_bus['sclk']
            cc_drivers_g[i][3] += led_panel_bus['sclk']
            cc_drivers_b[i][3] += led_panel_bus['sclk']

            cc_drivers_r[i][4] += led_panel_bus['latch']
            cc_drivers_g[i][4] += led_panel_bus['latch']
            cc_drivers_b[i][4] += led_panel_bus['latch']

            cc_drivers_r[i][21] += led_panel_bus['blank']
            cc_drivers_g[i][21] += led_panel_bus['blank']
            cc_drivers_b[i][21] += led_panel_bus['blank']

            cc_drivers_r[i][23] += place_part_inline(GND, res(
                value='0', PN='', Manf='Yageo'), )
            cc_drivers_g[i][23] += place_part_inline(GND, res(
                value='0', PN='', Manf='Yageo'), )
            cc_drivers_b[i][23] += place_part_inline(GND, res(
                value='0', PN='', Manf='Yageo'), )

            add_decoupling([cc_drivers_r[i][24], cc_drivers_g[i]
                           [24], cc_drivers_b[i][24]], c_100nF)

            for j in range(16):
                # connect the outputs
                pin_offset = 5
                cc_drivers_r[i][j+pin_offset] += leds_rbag[i*16+j][1]
                cc_drivers_g[i][j+pin_offset] += leds_rbag[i*16+j][4]
                cc_drivers_b[i][j+pin_offset] += leds_rbag[i*16+j][2]

        cc_drivers_r[2][22] += _led_panel_bus['_dr']
        cc_drivers_g[2][22] += _led_panel_bus['_dg']
        cc_drivers_b[2][22] += _led_panel_bus['_db']


# Instantiate the circuit and generate the netlist.
if __name__ == "__main__":
    skidl.lib_search_paths["kicad"].append("C:\git\glabs-library")
    LedPanel()
    generate_netlist()
    generate_xml()

    # Create a BOM
    # subprocess.Popen(['python', "C:\\Program Files\\KiCad\\bin\\scripting\\plugins\\bom_csv_grouped_by_value.py",
    #                   'panel.xml', "led-panel.csv"])
