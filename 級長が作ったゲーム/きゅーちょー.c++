#include "raylib.h"
#include "raymath.h"
#include <vector>
#include <cstdlib>
#include <ctime>
using namespace std;

const float scW = 1400;
const float scH = 700;

class enemy {
public:
    int up = 0;
    int fullhp = 0;
    int etype = 0;
    int value = 0;
    int e_coolbown = 0;
    float speed = 0.0f;
    float ex = 0.0f;
    float ey = 540.0f / 1400.0f * scW;
    float moved = 0.0f;
    bool attacked = 
}