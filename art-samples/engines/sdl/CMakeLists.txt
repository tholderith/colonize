cmake_minimum_required(VERSION 3.16)
project(colonize_sdl CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED IMPORTED_TARGET sdl2>=2.0.12 SDL2_image)

add_executable(colonize_sdl src/main.cpp src/scene.cpp)
target_include_directories(colonize_sdl PRIVATE third_party)
target_link_libraries(colonize_sdl PRIVATE PkgConfig::SDL2)
target_compile_options(colonize_sdl PRIVATE -Wall -Wextra)
# Fallback location of scene/layout.json (art-samples root) when it can't be found
# relative to the style dir.
get_filename_component(ART_SAMPLES_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
target_compile_definitions(colonize_sdl PRIVATE ART_SAMPLES_DIR="${ART_SAMPLES_DIR}")
