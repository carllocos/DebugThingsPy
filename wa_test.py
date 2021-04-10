if __name__ == "__main__":

    from web_assembly import WAModule
    mod = WAModule.from_file('examples/fac_case/fac.wat')
    mod.types[0]

