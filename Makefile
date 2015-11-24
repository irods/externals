.PHONY : all clean
.PHONY : autoconf avro boost clang cmake cpython jansson libarchive libs3 zeromq4-1 cppzmq

all : autoconf avro boost clang cmake cpython jansson libarchive libs3 zeromq4-1 cppzmq

packages.mk : Makefile versions.json build.py
	./build.py packagesfile

-include packages.mk

$(AUTOCONF_PACKAGE) :
	./build.py autoconf > autoconf.log
autoconf : $(AUTOCONF_PACKAGE)
autoconf_clean :
	@echo "Cleaning autoconf..."
	@rm -rf autoconf*
	@rm -rf $(AUTOCONF_PACKAGE)

$(AVRO_PACKAGE) : $(BOOST_PACKAGE) $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py avro > avro.log
avro : $(AVRO_PACKAGE)
avro_clean :
	@echo "Cleaning avro..."
	@rm -rf avro*
	@rm -rf $(AVRO_PACKAGE)

$(BOOST_PACKAGE) : $(CLANG_PACKAGE)
	./build.py boost > boost.log
boost : $(BOOST_PACKAGE)
boost_clean :
	@echo "Cleaning boost..."
	@rm -rf boost*
	@rm -rf $(BOOST_PACKAGE)

$(CLANG_PACKAGE) : $(CMAKE_PACKAGE) $(CPYTHON_PACKAGE)
	./build.py clang > clang.log
clang : $(CLANG_PACKAGE)
clang_clean :
	@echo "Cleaning clang..."
	@rm -rf clang*
	@rm -rf $(CLANG_PACKAGE)

$(CMAKE_PACKAGE) :
	./build.py cmake > cmake.log
cmake : $(CMAKE_PACKAGE)
cmake_clean :
	@echo "Cleaning cmake..."
	@rm -rf cmake*
	@rm -rf $(CMAKE_PACKAGE)

$(CPYTHON_PACKAGE) :
	./build.py cpython > cpython.log
cpython : $(CPYTHON_PACKAGE)
cpython_clean :
	@echo "Cleaning cpython..."
	@rm -rf cpython*
	@rm -rf $(CPYTHON_PACKAGE)

$(JANSSON_PACKAGE) : $(CLANG_PACKAGE)
	./build.py jansson > jansson.log
jansson : $(JANSSON_PACKAGE)
jansson_clean :
	@echo "Cleaning jansson..."
	@rm -rf jansson*
	@rm -rf $(JANSSON_PACKAGE)

$(LIBARCHIVE_PACKAGE) : $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py libarchive > libarchive.log
libarchive : $(LIBARCHIVE_PACKAGE)
libarchive_clean :
	@echo "Cleaning libarchive..."
	@rm -rf libarchive*
	@rm -rf $(LIBARCHIVE_PACKAGE)

$(LIBS3_PACKAGE): $(CLANG_PACKAGE)
	./build.py libs3 > libs3.log
libs3 : $(LIBS3_PACKAGE)
libs3_clean :
	@echo "Cleaning libs3..."
	@rm -rf libs3*
	@rm -rf $(LIBS3_PACKAGE)

$(ZEROMQ4-1_PACKAGE): $(CLANG_PACKAGE)
	./build.py zeromq4-1 > zeromq4-1.log
zeromq4-1 : $(ZEROMQ4-1_PACKAGE)
zeromq4-1_clean :
	@echo "Cleaning zeromq4-1..."
	@rm -rf zeromq4-1*
	@rm -rf $(ZEROMQ4-1_PACKAGE)

$(CPPZMQ_PACKAGE):
	./build.py cppzmq > cppzmq.log
cppzmq : $(CPPZMQ_PACKAGE)
cppzmq_clean :
	@echo "Cleaning cppzmq..."
	@rm -rf cppzmq"
	@rm -rf $(CPPZMQ_PACKAGE)

clean : autoconf_clean avro_clean boost_clean clang_clean cmake_clean cpython_clean jansson_clean libarchive_clean libs3_clean zeromq4-1_clean cppzmq_clean
	@echo "Cleaning generated files..."
	@rm -rf packages.mk
	@echo "Done."
